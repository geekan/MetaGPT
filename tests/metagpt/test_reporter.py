import ast
from contextlib import asynccontextmanager

import aiohttp.web
import pytest

from metagpt.logs import log_llm_stream
from metagpt.utils.report import (
    END_MARKER_NAME,
    BlockType,
    BrowserReporter,
    DocsReporter,
    EditorReporter,
    NotebookReporter,
    ServerReporter,
    TaskReporter,
    TerminalReporter,
)


class MockFileLLM:
    def __init__(self, data: str):
        self.data = data

    async def aask(self, *args, **kwargs) -> str:
        for i in self.data.splitlines(keepends=True):
            log_llm_stream(i)
        log_llm_stream("\n")
        return self.data


@asynccontextmanager
async def callback_server(http_server):
    callback_data = []

    async def handler(request):
        callback_data.append(await request.json())
        return aiohttp.web.json_response({})

    server, url = await http_server(handler)
    yield url, callback_data
    await server.stop()


@pytest.mark.asyncio
async def test_terminal_report(http_server):
    async with callback_server(http_server) as (url, callback_data):
        async with TerminalReporter(callback_url=url) as reporter:
            await reporter.async_report("ls -a", "cmd")
            await reporter.async_report("main.py\n", "output")
            await reporter.async_report("setup.py\n", "output")
    assert all(BlockType.TERMINAL is BlockType(i["block"]) for i in callback_data)
    assert all(i["uuid"] == callback_data[0]["uuid"] for i in callback_data[1:])
    assert "".join(i["value"] for i in callback_data if i["name"] != END_MARKER_NAME) == "ls -amain.py\nsetup.py\n"


@pytest.mark.asyncio
async def test_browser_report(http_server):
    img = b"\x89PNG\r\n\x1a\n\x00\x00"
    web_url = "https://docs.deepwisdom.ai"

    class AsyncPage:
        async def screenshot(self):
            return img

    async with callback_server(http_server) as (url, callback_data):
        async with BrowserReporter(callback_url=url) as reporter:
            await reporter.async_report(web_url, "url")
            await reporter.async_report(AsyncPage(), "page")

    assert all(BlockType.BROWSER is BlockType(i["block"]) for i in callback_data)
    assert all(i["uuid"] == callback_data[0]["uuid"] for i in callback_data[1:])
    assert len(callback_data) == 3
    assert callback_data[-1]["name"] == END_MARKER_NAME
    assert callback_data[0]["name"] == "url"
    assert callback_data[0]["value"] == web_url
    assert callback_data[1]["name"] == "page"
    assert ast.literal_eval(callback_data[1]["value"]) == img


@pytest.mark.asyncio
async def test_server_reporter(http_server):
    local_url = "http://127.0.0.1:8080/index.html"
    async with callback_server(http_server) as (url, callback_data):
        reporter = ServerReporter(callback_url=url)
        await reporter.async_report(local_url)
    assert all(BlockType.BROWSER_RT is BlockType(i["block"]) for i in callback_data)
    assert len(callback_data) == 1
    assert callback_data[0]["name"] == "local_url"
    assert callback_data[0]["value"] == local_url
    assert not callback_data[0]["is_chunk"]


@pytest.mark.asyncio
async def test_task_reporter(http_server):
    task = {"current_task_id": "", "tasks": []}
    async with callback_server(http_server) as (url, callback_data):
        reporter = TaskReporter(callback_url=url)
        await reporter.async_report(task)

    assert all(BlockType.TASK is BlockType(i["block"]) for i in callback_data)
    assert len(callback_data) == 1
    assert callback_data[0]["name"] == "object"
    assert callback_data[0]["value"] == task


@pytest.mark.asyncio
async def test_notebook_reporter(http_server):
    code = {
        "cell_type": "code",
        "execution_count": None,
        "id": "e1841c44",
        "metadata": {},
        "outputs": [],
        "source": ["\n", "import time\n", "print('will sleep 1s.')\n", "time.sleep(1)\n", "print('end.')\n", ""],
    }
    output1 = {"name": "stdout", "output_type": "stream", "text": ["will sleep 1s.\n"]}
    output2 = {"name": "stdout", "output_type": "stream", "text": ["will sleep 1s.\n"]}
    code_path = "/data/main.ipynb"
    async with callback_server(http_server) as (url, callback_data):
        async with NotebookReporter(callback_url=url) as reporter:
            await reporter.async_report(code, "content")
            await reporter.async_report(output1, "content")
            await reporter.async_report(output2, "content")
            await reporter.async_report(code_path, "path")

    assert all(BlockType.NOTEBOOK is BlockType(i["block"]) for i in callback_data)
    assert len(callback_data) == 5
    assert callback_data[-1]["name"] == END_MARKER_NAME
    assert callback_data[-2]["name"] == "path"
    assert callback_data[-2]["value"] == code_path
    assert all(i["uuid"] == callback_data[0]["uuid"] for i in callback_data[1:])
    assert [i["value"] for i in callback_data if i["name"] == "content"] == [code, output1, output2]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("data", "file_path", "meta", "block", "report_cls"),
    (
        (
            "## Language\n\nen_us\n\n## Programming Language\n\nPython\n\n## Original Requirements\n\nCreate a 2048 gam...",
            "/data/prd.md",
            {"type": "write_prd"},
            BlockType.DOCS,
            DocsReporter,
        ),
        (
            "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\nprint('Hello World')\n",
            "/data/main.py",
            {"type": "write_code"},
            BlockType.EDITOR,
            EditorReporter,
        ),
    ),
    ids=["test_docs_reporter", "test_editor_reporter"],
)
async def test_llm_stream_reporter(data, file_path, meta, block, report_cls, http_server):
    async with callback_server(http_server) as (url, callback_data):
        async with report_cls(callback_url=url, enable_llm_stream=True) as reporter:
            await reporter.async_report(meta, "meta")
            await MockFileLLM(data).aask("")
            await reporter.wait_llm_stream_report()
            await reporter.async_report(file_path, "path")
    assert callback_data
    assert all(block is BlockType(i["block"]) for i in callback_data)
    assert all(i["uuid"] == callback_data[0]["uuid"] for i in callback_data[1:])
    chunks, names = [], set()
    for i in callback_data:
        name = i["name"]
        names.add(name)
        if name == "meta":
            assert i["value"] == meta
        elif name == "path":
            assert i["value"] == file_path
        elif name == END_MARKER_NAME:
            pass
        elif name == "content":
            chunks.append(i["value"])
        else:
            raise ValueError
    assert "".join(chunks[:-1]) == data
    assert names == {"meta", "path", "content", END_MARKER_NAME}
