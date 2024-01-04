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
from typing import Optional

import pytest

from metagpt.config import CONFIG, Config
from metagpt.const import DEFAULT_WORKSPACE_ROOT, TEST_DATA_PATH
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.provider.openai_api import OpenAILLM
from metagpt.utils.git_repository import GitRepository


class MockLLM(OpenAILLM):
    rsp_cache: dict = {}

    async def original_aask(
        self,
        msg: str,
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        timeout=3,
        stream=True,
    ):
        """A copy of metagpt.provider.base_llm.BaseLLM.aask, we can't use super().aask because it will be mocked"""
        if system_msgs:
            message = self._system_msgs(system_msgs)
        else:
            message = [self._default_system_msg()] if self.use_system_prompt else []
        if format_msgs:
            message.extend(format_msgs)
        message.append(self._user_msg(msg))
        rsp = await self.acompletion_text(message, stream=stream, timeout=timeout)
        return rsp

    async def aask(
        self,
        msg: str,
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        timeout=3,
        stream=True,
    ) -> str:
        if msg not in self.rsp_cache:
            # Call the original unmocked method
            rsp = await self.original_aask(msg, system_msgs, format_msgs, timeout, stream)
            logger.info(f"Added '{rsp[:20]}' ... to response cache")
            self.rsp_cache[msg] = rsp
            return rsp
        else:
            logger.info("Use response cache")
            return self.rsp_cache[msg]


@pytest.fixture(scope="session")
def rsp_cache():
    # model_version = CONFIG.openai_api_model
    rsp_cache_file_path = TEST_DATA_PATH / "rsp_cache.json"  # read repo-provided
    new_rsp_cache_file_path = TEST_DATA_PATH / "rsp_cache_new.json"  # exporting a new copy
    if os.path.exists(rsp_cache_file_path):
        with open(rsp_cache_file_path, "r") as f1:
            rsp_cache_json = json.load(f1)
    else:
        rsp_cache_json = {}
    yield rsp_cache_json
    with open(new_rsp_cache_file_path, "w") as f2:
        json.dump(rsp_cache_json, f2, indent=4, ensure_ascii=False)


@pytest.fixture(scope="function")
def llm_mock(rsp_cache, mocker):
    llm = MockLLM()
    llm.rsp_cache = rsp_cache
    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", llm.aask)
    yield mocker


class Context:
    def __init__(self):
        self._llm_ui = None
        self._llm_api = LLM(provider=CONFIG.get_default_llm_provider_enum())

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
    _context = Context()

    yield _context.llm_api

    logger.info("Tearing down the test")


@pytest.fixture(scope="session")
def proxy():
    pattern = re.compile(
        rb"(?P<method>[a-zA-Z]+) (?P<uri>(\w+://)?(?P<host>[^\s\'\"<>\[\]{}|/:]+)(:(?P<port>\d+))?[^\s\'\"<>\[\]{}|]*) "
    )

    async def pipe(reader, writer):
        while not reader.at_eof():
            writer.write(await reader.read(2048))
        writer.close()

    async def handle_client(reader, writer):
        data = await reader.readuntil(b"\r\n\r\n")
        print(f"Proxy: {data}")  # checking with capfd fixture
        infos = pattern.match(data)
        host, port = infos.group("host"), infos.group("port")
        port = int(port) if port else 80
        remote_reader, remote_writer = await asyncio.open_connection(host, port)
        if data.startswith(b"CONNECT"):
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        else:
            remote_writer.write(data)
        await asyncio.gather(pipe(reader, remote_writer), pipe(remote_reader, writer))

    server = asyncio.get_event_loop().run_until_complete(asyncio.start_server(handle_client, "127.0.0.1", 0))
    return "http://{}:{}".format(*server.sockets[0].getsockname())


# see https://github.com/Delgan/loguru/issues/59#issuecomment-466591978
@pytest.fixture
def loguru_caplog(caplog):
    class PropogateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    logger.add(PropogateHandler(), format="{message}")
    yield caplog


# init & dispose git repo
@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_git_repo(request):
    CONFIG.git_repo = GitRepository(local_path=DEFAULT_WORKSPACE_ROOT / f"unittest/{uuid.uuid4().hex}")
    CONFIG.git_reinit = True

    # Destroy git repo at the end of the test session.
    def fin():
        CONFIG.git_repo.delete_repository()

    # Register the function for destroying the environment.
    request.addfinalizer(fin)


@pytest.fixture(scope="session", autouse=True)
def init_config():
    Config()


@pytest.fixture
def aiohttp_mocker(mocker):
    class MockAioResponse:
        async def json(self, *args, **kwargs):
            return self._json

        def set_json(self, json):
            self._json = json

    response = MockAioResponse()

    class MockCTXMng:
        async def __aenter__(self):
            return response

        async def __aexit__(self, *args, **kwargs):
            pass

        def __await__(self):
            yield
            return response

    def mock_request(self, method, url, **kwargs):
        return MockCTXMng()

    def wrap(method):
        def run(self, url, **kwargs):
            return mock_request(self, method, url, **kwargs)

        return run

    mocker.patch("aiohttp.ClientSession.request", mock_request)
    for i in ["get", "post", "delete", "patch"]:
        mocker.patch(f"aiohttp.ClientSession.{i}", wrap(i))

    yield response
