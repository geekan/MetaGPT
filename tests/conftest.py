#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/1 12:10
@Author  : alexanderwu
@File    : conftest.py
"""

import asyncio
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Callable

import aiohttp.web
import pytest

from metagpt.const import DEFAULT_WORKSPACE_ROOT, TEST_DATA_PATH
from metagpt.context import Context as MetagptContext
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.utils.git_repository import GitRepository
from metagpt.utils.project_repo import ProjectRepo
from tests.mock.mock_aiohttp import MockAioResponse
from tests.mock.mock_curl_cffi import MockCurlCffiResponse
from tests.mock.mock_httplib2 import MockHttplib2Response
from tests.mock.mock_llm import MockLLM

RSP_CACHE_NEW = {}  # used globally for producing new and useful only response cache
ALLOW_OPENAI_API_CALL = int(
    os.environ.get("ALLOW_OPENAI_API_CALL", 1)
)  # NOTE: should change to default 0 (False) once mock is complete


@pytest.fixture(scope="session")
def rsp_cache():
    rsp_cache_file_path = TEST_DATA_PATH / "rsp_cache.json"  # read repo-provided
    new_rsp_cache_file_path = TEST_DATA_PATH / "rsp_cache_new.json"  # exporting a new copy
    if os.path.exists(rsp_cache_file_path):
        with open(rsp_cache_file_path, "r", encoding="utf-8") as f1:
            rsp_cache_json = json.load(f1)
    else:
        rsp_cache_json = {}
    yield rsp_cache_json
    with open(rsp_cache_file_path, "w", encoding="utf-8") as f2:
        json.dump(rsp_cache_json, f2, indent=4, ensure_ascii=False)
    with open(new_rsp_cache_file_path, "w", encoding="utf-8") as f2:
        json.dump(RSP_CACHE_NEW, f2, indent=4, ensure_ascii=False)


# Hook to capture the test result
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        item.test_outcome = rep


@pytest.fixture(scope="function", autouse=True)
def llm_mock(rsp_cache, mocker, request):
    llm = MockLLM(allow_open_api_call=ALLOW_OPENAI_API_CALL)
    llm.rsp_cache = rsp_cache
    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", llm.aask)
    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask_batch", llm.aask_batch)
    mocker.patch("metagpt.provider.openai_api.OpenAILLM.aask_code", llm.aask_code)
    yield mocker
    if hasattr(request.node, "test_outcome") and request.node.test_outcome.passed:
        if llm.rsp_candidates:
            for rsp_candidate in llm.rsp_candidates:
                cand_key = list(rsp_candidate.keys())[0]
                cand_value = list(rsp_candidate.values())[0]
                if cand_key not in llm.rsp_cache:
                    logger.info(f"Added '{cand_key[:100]} ... -> {str(cand_value)[:20]} ...' to response cache")
                    llm.rsp_cache.update(rsp_candidate)
                RSP_CACHE_NEW.update(rsp_candidate)


class Context:
    def __init__(self):
        self._llm_ui = None
        self._llm_api = LLM()

    @property
    def llm_api(self):
        # 1. 初始化llm，带有缓存结果
        # 2. 如果缓存query，那么直接返回缓存结果
        # 3. 如果没有缓存query，那么调用llm_api，返回结果
        # 4. 如果有缓存query，那么更新缓存结果
        return self._llm_api


@pytest.fixture(scope="package")
def llm_api():
    logger.info("Setting up the test")
    g_context = Context()

    yield g_context.llm_api

    logger.info("Tearing down the test")


@pytest.fixture
def proxy():
    pattern = re.compile(
        rb"(?P<method>[a-zA-Z]+) (?P<uri>(\w+://)?(?P<host>[^\s\'\"<>\[\]{}|/:]+)(:(?P<port>\d+))?[^\s\'\"<>\[\]{}|]*) "
    )

    async def pipe(reader, writer):
        while not reader.at_eof():
            writer.write(await reader.read(2048))
        writer.close()
        await writer.wait_closed()

    async def handle_client(reader, writer):
        data = await reader.readuntil(b"\r\n\r\n")
        infos = pattern.match(data)
        host, port = infos.group("host"), infos.group("port")
        print(f"Proxy: {host}")  # checking with capfd fixture
        port = int(port) if port else 80
        remote_reader, remote_writer = await asyncio.open_connection(host, port)
        if data.startswith(b"CONNECT"):
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        else:
            remote_writer.write(data)
        await asyncio.gather(pipe(reader, remote_writer), pipe(remote_reader, writer))

    async def proxy_func():
        server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
        return server, "http://{}:{}".format(*server.sockets[0].getsockname())

    return proxy_func


# see https://github.com/Delgan/loguru/issues/59#issuecomment-466591978
@pytest.fixture
def loguru_caplog(caplog):
    class PropogateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    logger.add(PropogateHandler(), format="{message}")
    yield caplog


@pytest.fixture(scope="function")
def context(request):
    ctx = MetagptContext()
    ctx.git_repo = GitRepository(local_path=DEFAULT_WORKSPACE_ROOT / f"unittest/{uuid.uuid4().hex}")
    ctx.repo = ProjectRepo(ctx.git_repo)

    # Destroy git repo at the end of the test session.
    def fin():
        if ctx.git_repo:
            ctx.git_repo.delete_repository()

    # Register the function for destroying the environment.
    request.addfinalizer(fin)
    return ctx


@pytest.fixture(scope="session", autouse=True)
def init_config():
    pass


@pytest.fixture(scope="function")
def new_filename(mocker):
    # NOTE: Mock new filename to make reproducible llm aask, should consider changing after implementing requirement segmentation
    mocker.patch("metagpt.utils.file_repository.FileRepository.new_filename", lambda: "20240101")
    yield mocker


def _rsp_cache(name):
    rsp_cache_file_path = TEST_DATA_PATH / f"{name}.json"  # read repo-provided
    if os.path.exists(rsp_cache_file_path):
        with open(rsp_cache_file_path, "r") as f1:
            rsp_cache_json = json.load(f1)
    else:
        rsp_cache_json = {}
    yield rsp_cache_json
    with open(rsp_cache_file_path, "w") as f2:
        json.dump(rsp_cache_json, f2, indent=4, ensure_ascii=False)


@pytest.fixture(scope="session")
def search_rsp_cache():
    yield from _rsp_cache("search_rsp_cache")


@pytest.fixture(scope="session")
def mermaid_rsp_cache():
    yield from _rsp_cache("mermaid_rsp_cache")


@pytest.fixture
def aiohttp_mocker(mocker):
    MockResponse = type("MockResponse", (MockAioResponse,), {})

    def wrap(method):
        def run(self, url, **kwargs):
            return MockResponse(self, method, url, **kwargs)

        return run

    mocker.patch("aiohttp.ClientSession.request", MockResponse)
    for i in ["get", "post", "delete", "patch"]:
        mocker.patch(f"aiohttp.ClientSession.{i}", wrap(i))
    yield MockResponse


@pytest.fixture
def curl_cffi_mocker(mocker):
    MockResponse = type("MockResponse", (MockCurlCffiResponse,), {})

    def request(self, *args, **kwargs):
        return MockResponse(self, *args, **kwargs)

    mocker.patch("curl_cffi.requests.Session.request", request)
    yield MockResponse


@pytest.fixture
def httplib2_mocker(mocker):
    MockResponse = type("MockResponse", (MockHttplib2Response,), {})

    def request(self, *args, **kwargs):
        return MockResponse(self, *args, **kwargs)

    mocker.patch("httplib2.Http.request", request)
    yield MockResponse


@pytest.fixture
def search_engine_mocker(aiohttp_mocker, curl_cffi_mocker, httplib2_mocker, search_rsp_cache):
    # aiohttp_mocker: serpapi/serper
    # httplib2_mocker: google
    # curl_cffi_mocker: ddg
    check_funcs: dict[tuple[str, str], Callable[[dict], str]] = {}
    aiohttp_mocker.rsp_cache = httplib2_mocker.rsp_cache = curl_cffi_mocker.rsp_cache = search_rsp_cache
    aiohttp_mocker.check_funcs = httplib2_mocker.check_funcs = curl_cffi_mocker.check_funcs = check_funcs
    yield check_funcs


@pytest.fixture
def http_server():
    async def handler(request):
        return aiohttp.web.Response(
            text="""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
            <title>MetaGPT</title></head><body><h1>MetaGPT</h1></body></html>""",
            content_type="text/html",
        )

    async def start():
        server = aiohttp.web.Server(handler)
        runner = aiohttp.web.ServerRunner(server)
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        _, port, *_ = site._server.sockets[0].getsockname()
        return site, f"http://127.0.0.1:{port}"

    return start


@pytest.fixture
def mermaid_mocker(aiohttp_mocker, mermaid_rsp_cache):
    check_funcs: dict[tuple[str, str], Callable[[dict], str]] = {}
    aiohttp_mocker.rsp_cache = mermaid_rsp_cache
    aiohttp_mocker.check_funcs = check_funcs
    yield check_funcs


@pytest.fixture
def git_dir():
    """Fixture to get the unittest directory."""
    git_dir = Path(__file__).parent / f"unittest/{uuid.uuid4().hex}"
    git_dir.mkdir(parents=True, exist_ok=True)
    return git_dir
