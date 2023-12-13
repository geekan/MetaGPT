# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/17 14:22:15
@Author  :   orange-crow
@File    :   code_executor.py
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Tuple, Union
import traceback
import re

import nbformat
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_output
from rich.console import Console
from rich.syntax import Syntax

from metagpt.actions import Action
from metagpt.schema import Message
from metagpt.logs import logger


class ExecuteCode(ABC):
    @abstractmethod
    async def build(self):
        """build code executor"""
        ...

    @abstractmethod
    async def run(self, code: str):
        """run code"""
        ...

    @abstractmethod
    async def terminate(self):
        """terminate executor"""
        ...

    @abstractmethod
    async def reset(self):
        """reset executor"""
        ...


class ExecutePyCode(ExecuteCode, Action):
    """execute code, return result to llm, and display it."""

    def __init__(self, name: str = "python_executor", context=None, llm=None):
        super().__init__(name, context, llm)
        self.nb = nbformat.v4.new_notebook()
        self.nb_client = NotebookClient(self.nb)
        self.console = Console()
        self.interaction = "ipython" if self.is_ipython() else "terminal"

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
        self.nb_client = NotebookClient(self.nb)

    def add_code_cell(self, code):
        self.nb.cells.append(new_code_cell(source=code))

    def _display(self, code, language: str = "python"):
        if language == "python":
            code = Syntax(code, "python", theme="paraiso-dark", line_numbers=True)
            self.console.print("\n")
            self.console.print(code)

    def add_output_to_cell(self, cell, output):
        if "outputs" not in cell:
            cell["outputs"] = []
        # TODO: show figures
        else:
            cell["outputs"].append(new_output(output_type="stream", name="stdout", text=str(output)))

    def parse_outputs(self, outputs: List) -> str:
        assert isinstance(outputs, list)
        parsed_output = ""

        # empty outputs: such as 'x=1\ny=2'
        if not outputs:
            return parsed_output

        for i, output in enumerate(outputs):
            if output["output_type"] == "stream":
                parsed_output += output["text"]
            elif output["output_type"] == "display_data":
                if "image/png" in output["data"]:
                    self.show_bytes_figure(output["data"]["image/png"], self.interaction)
                else:
                    logger.info(f"{i}th output['data'] from nbclient outputs dont have image/png, continue next output ...")
            elif output["output_type"] == "execute_result":
                parsed_output += output["data"]["text/plain"]
        return parsed_output

    def show_bytes_figure(self, image_base64: str, interaction_type: str = "ipython"):
        import base64

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
            # 如果在Python脚本中运行，__file__ 变量存在
            return False

    def _process_code(self, code: Union[str, Dict, Message], language: str = None) -> Tuple:
        language = language or 'python'
        if isinstance(code, str) and Path(code).suffix in (".py", ".txt"):
            code = Path(code).read_text(encoding="utf-8")
            return code, language

        if isinstance(code, str):
            return code, language
        if isinstance(code, dict):
            assert "code" in code
            if "language" not in code:
                code['language'] = 'python'
            code, language = code["code"], code["language"]
        elif isinstance(code, Message):
            if isinstance(code.content, dict) and "language" not in code.content:
                code.content["language"] = 'python'
                code, language = code.content["code"], code.content["language"]
            elif isinstance(code.content, str):
                code, language = code.content, language
        else:
            raise ValueError(f"Not support code type {type(code).__name__}.")

        return code, language

    def save_notebook(self, path: str):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        nbformat.write(self.nb, path)

    async def run(self, code: Union[str, Dict, Message], language: str = "python") -> Tuple[str, bool]:
        code, language = self._process_code(code, language)

        self._display(code, language)

        if language == "python":
            # add code to the notebook
            self.add_code_cell(code=code)
            try:
                # build code executor
                await self.build()
                # run code
                # TODO: add max_tries for run code.
                cell_index = len(self.nb.cells) - 1
                await self.nb_client.async_execute_cell(self.nb.cells[-1], cell_index)
                outputs = self.parse_outputs(self.nb.cells[-1].outputs)
                success = True
            except Exception as e:
                outputs = traceback.format_exc()
                success = False
            return truncate(remove_escape_and_color_codes(outputs)), success
        else:
            # TODO: markdown
            raise NotImplementedError(f"Not support this code type : {language}, Only support code!")


def truncate(result: str, keep_len: int = 2000) -> str:
    desc = f"Truncated to show only the last {keep_len} characters\n"
    if result.startswith(desc):
        result = result[len(desc) :]

    if len(result) > keep_len:
        result = result[-keep_len:]
        return desc + result

    return result


def remove_escape_and_color_codes(input_str):
    # 使用正则表达式去除转义字符和颜色代码
    pattern = re.compile(r'\x1b\[[0-9;]*[mK]')
    result = pattern.sub('', input_str)
    return result
