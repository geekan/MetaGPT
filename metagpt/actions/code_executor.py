# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/17 14:22:15
@Author  :   orange-crow
@File    :   code_executor.py
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Tuple, Union

import nbformat
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_output
from rich.console import Console
from rich.syntax import Syntax

from metagpt.actions import Action
from metagpt.schema import Message


class CodeExecutor(ABC):
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


class PyCodeExecutor(CodeExecutor, Action):
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

        for output in outputs:
            if output["output_type"] == "stream":
                parsed_output += output["text"]
            elif output["output_type"] == "display_data":
                self.show_bytes_figure(output["data"]["image/png"], self.interaction)
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
        if isinstance(code, str) and Path(code).suffix in (".py", ".txt"):
            code = Path(code).read_text(encoding="utf-8")
            return code, language

        if isinstance(code, str):
            return code, language

        if isinstance(code, dict):
            assert "code" in code
            assert "language" in code
            code, language = code["code"], code["language"]
        elif isinstance(code, Message):
            assert "language" in code.content
            code, language = code.content["code"], code.content["language"]
        else:
            raise ValueError(f"Not support code type {type(code).__name__}.")

        return code, language

    async def run(self, code: Union[str, Dict, Message], language: str = "python") -> Message:
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
                return Message(
                    self.parse_outputs(self.nb.cells[-1].outputs), state="done", sent_from=self.__class__.__name__
                )
            except Exception as e:
                # FIXME: CellExecutionError is hard to read. for example `1\0` raise ZeroDivisionError:
                #  CellExecutionError('An error occurred while executing the following cell:\n------------------\nz=1/0\n------------------\n\n\n\x1b[0;31m---------------------------------------------------------------------------\x1b[0m\n\x1b[0;31mZeroDivisionError\x1b[0m                         Traceback (most recent call last)\nCell \x1b[0;32mIn[1], line 1\x1b[0m\n\x1b[0;32m----> 1\x1b[0m z\x1b[38;5;241m=\x1b[39m\x1b[38;5;241;43m1\x1b[39;49m\x1b[38;5;241;43m/\x1b[39;49m\x1b[38;5;241;43m0\x1b[39;49m\n\n\x1b[0;31mZeroDivisionError\x1b[0m: division by zero\n')
                return Message(e, state="error", sent_from=self.__class__.__name__)
        else:
            # TODO: markdown
            raise NotImplementedError(f"Not support this code type : {language}, Only support code!")
