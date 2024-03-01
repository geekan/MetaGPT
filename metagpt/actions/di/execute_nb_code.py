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
import traceback
from typing import Literal, Tuple

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellTimeoutError, DeadKernelError
from nbformat import NotebookNode
from nbformat.v4 import new_code_cell, new_markdown_cell, new_output
from rich.box import MINIMAL
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from metagpt.actions import Action
from metagpt.logs import logger


class ExecuteNbCode(Action):
    """execute notebook code block, return result to llm, and display it."""

    nb: NotebookNode
    nb_client: NotebookClient
    console: Console
    interaction: str
    timeout: int = 600

    def __init__(
        self,
        nb=nbformat.v4.new_notebook(),
        timeout=600,
    ):
        super().__init__(
            nb=nb,
            nb_client=NotebookClient(nb, timeout=timeout),
            timeout=timeout,
            console=Console(),
            interaction=("ipython" if self.is_ipython() else "terminal"),
        )

    async def build(self):
        if self.nb_client.kc is None or not await self.nb_client.kc.is_alive():
            self.nb_client.create_kernel_manager()
            self.nb_client.start_new_kernel()
            self.nb_client.start_new_kernel_client()

    async def terminate(self):
        """kill NotebookClient"""
        await self.nb_client._async_cleanup_kernel()

    async def reset(self):
        """reset NotebookClient"""
        await self.terminate()

        # sleep 1s to wait for the kernel to be cleaned up completely
        await asyncio.sleep(1)
        await self.build()
        self.nb_client = NotebookClient(self.nb, timeout=self.timeout)

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

    def parse_outputs(self, outputs: list[str]) -> str:
        """Parses the outputs received from notebook execution."""
        assert isinstance(outputs, list)
        parsed_output = ""

        for i, output in enumerate(outputs):
            if output["output_type"] == "stream" and not any(
                tag in output["text"]
                for tag in ["| INFO     | metagpt", "| ERROR    | metagpt", "| WARNING  | metagpt", "DEBUG"]
            ):
                parsed_output += output["text"]
            elif output["output_type"] == "display_data":
                if "image/png" in output["data"]:
                    self.show_bytes_figure(output["data"]["image/png"], self.interaction)
                else:
                    logger.info(
                        f"{i}th output['data'] from nbclient outputs dont have image/png, continue next output ..."
                    )
            elif output["output_type"] == "execute_result":
                parsed_output += output["data"]["text/plain"]
        return parsed_output

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
        try:
            await self.nb_client.async_execute_cell(cell, cell_index)
            return True, ""
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
            return False, f"{traceback.format_exc()}"

    async def run(self, code: str, language: Literal["python", "markdown"] = "python") -> Tuple[str, bool]:
        """
        return the output of code execution, and a success indicator (bool) of code execution.
        """
        self._display(code, language)

        if language == "python":
            # add code to the notebook
            self.add_code_cell(code=code)

            # build code executor
            await self.build()

            # run code
            cell_index = len(self.nb.cells) - 1
            success, error_message = await self.run_cell(self.nb.cells[-1], cell_index)

            if not success:
                return truncate(remove_escape_and_color_codes(error_message), is_success=success)

            # code success
            outputs = self.parse_outputs(self.nb.cells[-1].outputs)
            outputs, success = truncate(remove_escape_and_color_codes(outputs), is_success=success)

            if "!pip" in code:
                success = False

            return outputs, success

        elif language == "markdown":
            # add markdown content to markdown cell in a notebook.
            self.add_markdown_cell(code)
            # return True, beacuse there is no execution failure for markdown cell.
            return code, True
        else:
            raise ValueError(f"Only support for language: python, markdown, but got {language}, ")


def truncate(result: str, keep_len: int = 2000, is_success: bool = True):
    """对于超出keep_len个字符的result: 执行失败的代码, 展示result后keep_len个字符; 执行成功的代码, 展示result前keep_len个字符。"""
    if is_success:
        desc = f"Executed code successfully. Truncated to show only first {keep_len} characters\n"
    else:
        desc = f"Executed code failed, please reflect the cause of bug and then debug. Truncated to show only last {keep_len} characters\n"

    if result.strip().startswith("<coroutine object"):
        result = "Executed code failed, you need use key word 'await' to run a async code."
        return result, False

    if len(result) > keep_len:
        result = result[-keep_len:] if not is_success else result[:keep_len]
        return desc + result, is_success

    return result, is_success


def remove_escape_and_color_codes(input_str: str):
    # 使用正则表达式去除转义字符和颜色代码
    pattern = re.compile(r"\x1b\[[0-9;]*[mK]")
    result = pattern.sub("", input_str)
    return result


def display_markdown(content: str):
    # 使用正则表达式逐个匹配代码块
    matches = re.finditer(r"```(.+?)```", content, re.DOTALL)
    start_index = 0
    content_panels = []
    # 逐个打印匹配到的文本和代码
    for match in matches:
        text_content = content[start_index : match.start()].strip()
        code_content = match.group(0).strip()[3:-3]  # Remove triple backticks

        if text_content:
            content_panels.append(Panel(Markdown(text_content), box=MINIMAL))

        if code_content:
            content_panels.append(Panel(Markdown(f"```{code_content}"), box=MINIMAL))
        start_index = match.end()

    # 打印剩余文本（如果有）
    remaining_text = content[start_index:].strip()
    if remaining_text:
        content_panels.append(Panel(Markdown(remaining_text), box=MINIMAL))

    # 在Live模式中显示所有Panel
    with Live(auto_refresh=False, console=Console(), vertical_overflow="visible") as live:
        live.update(Group(*content_panels))
        live.refresh()
