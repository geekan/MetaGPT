# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/17 14:22:15
@Author  :   orange-crow
@File    :   execute_nb_code.py
"""
from __future__ import annotations

import asyncio
import base64
import re
from typing import Literal, Tuple

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionComplete, CellTimeoutError, DeadKernelError
from nbclient.util import ensure_async
from nbformat import NotebookNode
from nbformat.v4 import new_code_cell, new_markdown_cell, new_output, output_from_msg
from rich.box import MINIMAL
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.report import NotebookReporter

INSTALL_KEEPLEN = 500
INI_CODE = """import warnings
import logging

root_logger = logging.getLogger()
root_logger.setLevel(logging.ERROR)
warnings.filterwarnings('ignore')"""


class RealtimeOutputNotebookClient(NotebookClient):
    """Realtime output of Notebook execution."""

    def __init__(self, *args, notebook_reporter=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.notebook_reporter = notebook_reporter or NotebookReporter()

    async def _async_poll_output_msg(self, parent_msg_id: str, cell: NotebookNode, cell_index: int) -> None:
        """Implement a feature to enable sending messages."""
        assert self.kc is not None
        while True:
            msg = await ensure_async(self.kc.iopub_channel.get_msg(timeout=None))
            await self._send_msg(msg)

            if msg["parent_header"].get("msg_id") == parent_msg_id:
                try:
                    # Will raise CellExecutionComplete when completed
                    self.process_message(msg, cell, cell_index)
                except CellExecutionComplete:
                    return

    async def _send_msg(self, msg: dict):
        msg_type = msg.get("header", {}).get("msg_type")
        if msg_type not in ["stream", "error", "execute_result"]:
            return

        await self.notebook_reporter.async_report(output_from_msg(msg), "content")


class ExecuteNbCode(Action):
    """execute notebook code block, return result to llm, and display it."""

    nb: NotebookNode
    nb_client: RealtimeOutputNotebookClient = None
    console: Console
    interaction: str
    timeout: int = 600

    def __init__(self, nb=nbformat.v4.new_notebook(), timeout=600):
        super().__init__(
            nb=nb,
            timeout=timeout,
            console=Console(),
            interaction=("ipython" if self.is_ipython() else "terminal"),
        )
        self.reporter = NotebookReporter()
        self.set_nb_client()
        self.init_called = False

    async def init_code(self):
        if not self.init_called:
            await self.run(INI_CODE)
            self.init_called = True

    def set_nb_client(self):
        self.nb_client = RealtimeOutputNotebookClient(
            self.nb,
            timeout=self.timeout,
            resources={"metadata": {"path": self.config.workspace.path}},
            notebook_reporter=self.reporter,
            coalesce_streams=True,
        )

    async def build(self):
        if self.nb_client.kc is None or not await self.nb_client.kc.is_alive():
            self.nb_client.create_kernel_manager()
            self.nb_client.start_new_kernel()
            self.nb_client.start_new_kernel_client()

    async def terminate(self):
        """kill NotebookClient"""
        if self.nb_client.km is not None and await self.nb_client.km.is_alive():
            await self.nb_client.km.shutdown_kernel(now=True)
            await self.nb_client.km.cleanup_resources()

            channels = [
                self.nb_client.kc.stdin_channel,  # The channel for handling standard input to the kernel.
                self.nb_client.kc.hb_channel,  # The channel for heartbeat communication between the kernel and client.
                self.nb_client.kc.control_channel,  # The channel for controlling the kernel.
            ]

            # Stops all the running channels for this kernel
            for channel in channels:
                if channel.is_alive():
                    channel.stop()

            self.nb_client.kc = None
            self.nb_client.km = None

    async def reset(self):
        """reset NotebookClient"""
        await self.terminate()

        # sleep 1s to wait for the kernel to be cleaned up completely
        await asyncio.sleep(1)
        await self.build()
        self.set_nb_client()

    def add_code_cell(self, code: str):
        self.nb.cells.append(new_code_cell(source=code))

    def add_markdown_cell(self, markdown: str):
        self.nb.cells.append(new_markdown_cell(source=markdown))

    def _display(self, code: str, language: Literal["python", "markdown"] = "python"):
        if language == "python":
            code = Syntax(code, "python", theme="paraiso-dark", line_numbers=True)
            self.console.print(code)
        elif language == "markdown":
            display_markdown(code)
        else:
            raise ValueError(f"Only support for python, markdown, but got {language}")

    def add_output_to_cell(self, cell: NotebookNode, output: str):
        """add outputs of code execution to notebook cell."""
        if "outputs" not in cell:
            cell["outputs"] = []
        else:
            cell["outputs"].append(new_output(output_type="stream", name="stdout", text=str(output)))

    def parse_outputs(self, outputs: list[str], keep_len: int = 5000) -> Tuple[bool, str]:
        """Parses the outputs received from notebook execution."""
        assert isinstance(outputs, list)
        parsed_output, is_success = [], True
        for i, output in enumerate(outputs):
            output_text = ""
            if output["output_type"] == "stream" and not any(
                tag in output["text"]
                for tag in ["| INFO     | metagpt", "| ERROR    | metagpt", "| WARNING  | metagpt", "DEBUG"]
            ):
                output_text = output["text"]
            elif output["output_type"] == "display_data":
                if "image/png" in output["data"]:
                    self.show_bytes_figure(output["data"]["image/png"], self.interaction)
                else:
                    logger.info(
                        f"{i}th output['data'] from nbclient outputs dont have image/png, continue next output ..."
                    )
            elif output["output_type"] == "execute_result":
                output_text = output["data"]["text/plain"]
            elif output["output_type"] == "error":
                output_text, is_success = "\n".join(output["traceback"]), False

            # handle coroutines that are not executed asynchronously
            if output_text.strip().startswith("<coroutine object"):
                output_text = "Executed code failed, you need use key word 'await' to run a async code."
                is_success = False

            output_text = remove_escape_and_color_codes(output_text)
            if is_success:
                output_text = remove_log_and_warning_lines(output_text)
            # The useful information of the exception is at the end,
            # the useful information of normal output is at the begining.
            if "<!DOCTYPE html>" not in output_text:
                output_text = output_text[:keep_len] if is_success else output_text[-keep_len:]

            parsed_output.append(output_text)
        return is_success, ",".join(parsed_output)

    def show_bytes_figure(self, image_base64: str, interaction_type: Literal["ipython", None]):
        image_bytes = base64.b64decode(image_base64)
        if interaction_type == "ipython":
            from IPython.display import Image, display

            display(Image(data=image_bytes))
        else:
            import io

            from PIL import Image

            image = Image.open(io.BytesIO(image_bytes))
            image.show()

    def is_ipython(self) -> bool:
        try:
            # 如果在Jupyter Notebook中运行，__file__ 变量不存在
            from IPython import get_ipython

            if get_ipython() is not None and "IPKernelApp" in get_ipython().config:
                return True
            else:
                return False
        except NameError:
            return False

    async def run_cell(self, cell: NotebookNode, cell_index: int) -> Tuple[bool, str]:
        """set timeout for run code.
        returns the success or failure of the cell execution, and an optional error message.
        """
        await self.reporter.async_report(cell, "content")

        try:
            await self.nb_client.async_execute_cell(cell, cell_index)
            return self.parse_outputs(self.nb.cells[-1].outputs)
        except CellTimeoutError:
            assert self.nb_client.km is not None
            await self.nb_client.km.interrupt_kernel()
            await asyncio.sleep(1)
            error_msg = "Cell execution timed out: Execution exceeded the time limit and was stopped; consider optimizing your code for better performance."
            return False, error_msg
        except DeadKernelError:
            await self.reset()
            return False, "DeadKernelError"
        except Exception:
            return self.parse_outputs(self.nb.cells[-1].outputs)

    async def run(self, code: str, language: Literal["python", "markdown"] = "python") -> Tuple[str, bool]:
        """
        return the output of code execution, and a success indicator (bool) of code execution.
        """
        self._display(code, language)

        async with self.reporter:
            if language == "python":
                # add code to the notebook
                self.add_code_cell(code=code)

                # build code executor
                await self.build()

                # run code
                cell_index = len(self.nb.cells) - 1
                success, outputs = await self.run_cell(self.nb.cells[-1], cell_index)

                if "!pip" in code:
                    success = False
                    outputs = outputs[-INSTALL_KEEPLEN:]
                elif "git clone" in code:
                    outputs = outputs[:INSTALL_KEEPLEN] + "..." + outputs[-INSTALL_KEEPLEN:]

            elif language == "markdown":
                # add markdown content to markdown cell in a notebook.
                self.add_markdown_cell(code)
                # return True, beacuse there is no execution failure for markdown cell.
                outputs, success = code, True
            else:
                raise ValueError(f"Only support for language: python, markdown, but got {language}, ")

            file_path = self.config.workspace.path / "code.ipynb"
            nbformat.write(self.nb, file_path)
            await self.reporter.async_report(file_path, "path")

            return outputs, success


def remove_log_and_warning_lines(input_str: str) -> str:
    delete_lines = ["[warning]", "warning:", "[cv]", "[info]"]
    result = "\n".join(
        [line for line in input_str.split("\n") if not any(dl in line.lower() for dl in delete_lines)]
    ).strip()
    return result


def remove_escape_and_color_codes(input_str: str):
    # 使用正则表达式去除jupyter notebook输出结果中的转义字符和颜色代码
    # Use regular expressions to get rid of escape characters and color codes in jupyter notebook output.
    pattern = re.compile(r"\x1b\[[0-9;]*[mK]")
    result = pattern.sub("", input_str)
    return result


def display_markdown(content: str):
    # Use regular expressions to match blocks of code one by one.
    matches = re.finditer(r"```(.+?)```", content, re.DOTALL)
    start_index = 0
    content_panels = []
    # Set the text background color and text color.
    style = "black on white"
    # Print the matching text and code one by one.
    for match in matches:
        text_content = content[start_index : match.start()].strip()
        code_content = match.group(0).strip()[3:-3]  # Remove triple backticks

        if text_content:
            content_panels.append(Panel(Markdown(text_content), style=style, box=MINIMAL))

        if code_content:
            content_panels.append(Panel(Markdown(f"```{code_content}"), style=style, box=MINIMAL))
        start_index = match.end()

    # Print remaining text (if any).
    remaining_text = content[start_index:].strip()
    if remaining_text:
        content_panels.append(Panel(Markdown(remaining_text), style=style, box=MINIMAL))

    # Display all panels in Live mode.
    with Live(auto_refresh=False, console=Console(), vertical_overflow="visible") as live:
        live.update(Group(*content_panels))
        live.refresh()
