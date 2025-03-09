import asyncio
import os
import typing
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Literal, Optional, Union
from urllib.parse import unquote, urlparse, urlunparse
from uuid import UUID, uuid4

from aiohttp import ClientSession, UnixConnector
from playwright.async_api import Page as AsyncPage
from playwright.sync_api import Page as SyncPage
from pydantic import BaseModel, Field, PrivateAttr

from metagpt.const import METAGPT_REPORTER_DEFAULT_URL
from metagpt.logs import create_llm_stream_queue, get_llm_stream_queue

if typing.TYPE_CHECKING:
    from metagpt.roles.role import Role

try:
    import requests_unixsocket as requests
except ImportError:
    import requests

from contextvars import ContextVar

CURRENT_ROLE: ContextVar["Role"] = ContextVar("role")


class BlockType(str, Enum):
    """Enumeration for different types of blocks."""

    TERMINAL = "Terminal"
    TASK = "Task"
    BROWSER = "Browser"
    BROWSER_RT = "Browser-RT"
    EDITOR = "Editor"
    GALLERY = "Gallery"
    NOTEBOOK = "Notebook"
    DOCS = "Docs"
    THOUGHT = "Thought"


END_MARKER_NAME = "end_marker"
END_MARKER_VALUE = "\x18\x19\x1B\x18\n"


class ResourceReporter(BaseModel):
    """Base class for resource reporting."""

    block: BlockType = Field(description="The type of block that is reporting the resource")
    uuid: UUID = Field(default_factory=uuid4, description="The unique identifier for the resource")
    enable_llm_stream: bool = Field(False, description="Indicates whether to connect to an LLM stream for reporting")
    callback_url: str = Field(METAGPT_REPORTER_DEFAULT_URL, description="The URL to which the report should be sent")
    _llm_task: Optional[asyncio.Task] = PrivateAttr(None)

    def report(self, value: Any, name: str, extra: Optional[dict] = None):
        """Synchronously report resource observation data.

        Args:
            value: The data to report.
            name: The type name of the data.
        """
        return self._report(value, name, extra)

    async def async_report(self, value: Any, name: str, extra: Optional[dict] = None):
        """Asynchronously report resource observation data.

        Args:
            value: The data to report.
            name: The type name of the data.
        """
        return await self._async_report(value, name, extra)

    @classmethod
    def set_report_fn(cls, fn: Callable):
        """Set the synchronous report function.

        Args:
            fn: A callable function used for synchronous reporting. For example:

                >>> def _report(self, value: Any, name: str):
                ...     print(value, name)

        """
        cls._report = fn

    @classmethod
    def set_async_report_fn(cls, fn: Callable):
        """Set the asynchronous report function.

        Args:
            fn: A callable function used for asynchronous reporting. For example:

                ```python
                >>> async def _report(self, value: Any, name: str):
                ...     print(value, name)
                ```
        """
        cls._async_report = fn

    def _report(self, value: Any, name: str, extra: Optional[dict] = None):
        if not self.callback_url:
            return

        data = self._format_data(value, name, extra)
        resp = requests.post(self.callback_url, json=data)
        resp.raise_for_status()
        return resp.text

    async def _async_report(self, value: Any, name: str, extra: Optional[dict] = None):
        if not self.callback_url:
            return

        data = self._format_data(value, name, extra)
        url = self.callback_url
        _result = urlparse(url)
        sessiion_kwargs = {}
        if _result.scheme.endswith("+unix"):
            parsed_list = list(_result)
            parsed_list[0] = parsed_list[0][:-5]
            parsed_list[1] = "fake.org"
            url = urlunparse(parsed_list)
            sessiion_kwargs["connector"] = UnixConnector(path=unquote(_result.netloc))

        async with ClientSession(**sessiion_kwargs) as client:
            async with client.post(url, json=data) as resp:
                resp.raise_for_status()
                return await resp.text()

    def _format_data(self, value, name, extra):
        data = self.model_dump(mode="json", exclude=("callback_url", "llm_stream"))
        if isinstance(value, BaseModel):
            value = value.model_dump(mode="json")
        elif isinstance(value, Path):
            value = str(value)

        if name == "path":
            value = os.path.abspath(value)
        data["value"] = value
        data["name"] = name
        role = CURRENT_ROLE.get(None)
        if role:
            role_name = role.name
        else:
            role_name = os.environ.get("METAGPT_ROLE")
        data["role"] = role_name
        if extra:
            data["extra"] = extra
        return data

    def __enter__(self):
        """Enter the synchronous streaming callback context."""
        return self

    def __exit__(self, *args, **kwargs):
        """Exit the synchronous streaming callback context."""
        self.report(None, END_MARKER_NAME)

    async def __aenter__(self):
        """Enter the asynchronous streaming callback context."""
        if self.enable_llm_stream:
            queue = create_llm_stream_queue()
            self._llm_task = asyncio.create_task(self._llm_stream_report(queue))
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        """Exit the asynchronous streaming callback context."""
        if self.enable_llm_stream and exc_type != asyncio.CancelledError:
            await get_llm_stream_queue().put(None)
            await self._llm_task
            self._llm_task = None
        await self.async_report(None, END_MARKER_NAME)

    async def _llm_stream_report(self, queue: asyncio.Queue):
        while True:
            data = await queue.get()
            if data is None:
                return
            await self.async_report(data, "content")

    async def wait_llm_stream_report(self):
        """Wait for the LLM stream report to complete."""
        queue = get_llm_stream_queue()
        while self._llm_task:
            if queue.empty():
                break
            await asyncio.sleep(0.01)


class TerminalReporter(ResourceReporter):
    """Terminal output callback for streaming reporting of command and output.

    The terminal has state, and an agent can open multiple terminals and input different commands into them.
    To correctly display these states, each terminal should have its own unique ID, so in practice, each terminal
    should instantiate its own TerminalReporter object.
    """

    block: Literal[BlockType.TERMINAL] = BlockType.TERMINAL

    def report(self, value: str, name: Literal["cmd", "output"]):
        """Report terminal command or output synchronously."""
        return super().report(value, name)

    async def async_report(self, value: str, name: Literal["cmd", "output"]):
        """Report terminal command or output asynchronously."""
        return await super().async_report(value, name)


class BrowserReporter(ResourceReporter):
    """Browser output callback for streaming reporting of requested URL and page content.

    The browser has state, so in practice, each browser should instantiate its own BrowserReporter object.
    """

    block: Literal[BlockType.BROWSER] = BlockType.BROWSER

    def report(self, value: Union[str, SyncPage], name: Literal["url", "page"]):
        """Report browser URL or page content synchronously."""
        if name == "page":
            value = {"page_url": value.url, "title": value.title(), "screenshot": str(value.screenshot())}
        return super().report(value, name)

    async def async_report(self, value: Union[str, AsyncPage], name: Literal["url", "page"]):
        """Report browser URL or page content asynchronously."""
        if name == "page":
            value = {"page_url": value.url, "title": await value.title(), "screenshot": str(await value.screenshot())}
        return await super().async_report(value, name)


class ServerReporter(ResourceReporter):
    """Callback for server deployment reporting."""

    block: Literal[BlockType.BROWSER_RT] = BlockType.BROWSER_RT

    def report(self, value: str, name: Literal["local_url"] = "local_url"):
        """Report server deployment synchronously."""
        return super().report(value, name)

    async def async_report(self, value: str, name: Literal["local_url"] = "local_url"):
        """Report server deployment asynchronously."""
        return await super().async_report(value, name)


class ObjectReporter(ResourceReporter):
    """Callback for reporting complete object resources."""

    def report(self, value: dict, name: Literal["object"] = "object"):
        """Report object resource synchronously."""
        return super().report(value, name)

    async def async_report(self, value: dict, name: Literal["object"] = "object"):
        """Report object resource asynchronously."""
        return await super().async_report(value, name)


class TaskReporter(ObjectReporter):
    """Reporter for object resources to Task Block."""

    block: Literal[BlockType.TASK] = BlockType.TASK


class ThoughtReporter(ObjectReporter):
    """Reporter for object resources to Task Block."""

    block: Literal[BlockType.THOUGHT] = BlockType.THOUGHT


class FileReporter(ResourceReporter):
    """File resource callback for reporting complete file paths.

    There are two scenarios: if the file needs to be output in its entirety at once, use non-streaming callback;
    if the file can be partially output for display first, use streaming callback.
    """

    def report(
        self,
        value: Union[Path, dict, Any],
        name: Literal["path", "meta", "content"] = "path",
        extra: Optional[dict] = None,
    ):
        """Report file resource synchronously."""
        return super().report(value, name, extra)

    async def async_report(
        self,
        value: Union[Path, dict, Any],
        name: Literal["path", "meta", "content"] = "path",
        extra: Optional[dict] = None,
    ):
        """Report file resource asynchronously."""
        return await super().async_report(value, name, extra)


class NotebookReporter(FileReporter):
    """Equivalent to FileReporter(block=BlockType.NOTEBOOK)."""

    block: Literal[BlockType.NOTEBOOK] = BlockType.NOTEBOOK


class DocsReporter(FileReporter):
    """Equivalent to FileReporter(block=BlockType.DOCS)."""

    block: Literal[BlockType.DOCS] = BlockType.DOCS


class EditorReporter(FileReporter):
    """Equivalent to FileReporter(block=BlockType.EDITOR)."""

    block: Literal[BlockType.EDITOR] = BlockType.EDITOR


class GalleryReporter(FileReporter):
    """Image resource callback for reporting complete file paths.

    Since images need to be complete before display, each callback is a complete file path. However, the Gallery
    needs to display the type of image and prompt, so if there is meta information, it should be reported in a
    streaming manner.
    """

    block: Literal[BlockType.GALLERY] = BlockType.GALLERY

    def report(self, value: Union[dict, Path], name: Literal["meta", "path"] = "path"):
        """Report image resource synchronously."""
        return super().report(value, name)

    async def async_report(self, value: Union[dict, Path], name: Literal["meta", "path"] = "path"):
        """Report image resource asynchronously."""
        return await super().async_report(value, name)
