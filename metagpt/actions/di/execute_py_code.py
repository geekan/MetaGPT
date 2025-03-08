# -*- encoding: utf-8 -*-
"""
@Date    :   2024/11/14 22:48:29
@Author  :   orange-crow
@File    :   execute_py_code.py
"""

import re
import textwrap
from collections import OrderedDict
from typing import Literal

from metagpt.actions import Action
from metagpt.tools.code_executor.display import print_text_live
from metagpt.tools.code_executor.pyexe import AsyncPyExecutor


class ExecutePyCode(Action):
    """execute python code, return result to llm, and display it."""

    is_save_obj: bool
    work_dir: str
    executor: AsyncPyExecutor

    def __init__(self, is_save_obj: bool = False, work_dir: str = ""):
        super().__init__(
            is_save_obj=is_save_obj,  # to save python object in code.
            work_dir=work_dir,  # python object saved dir.
            executor=AsyncPyExecutor(work_dir, is_save_obj),
        )

    async def build(self):
        self.code_gen = self.executor.run()
        await self.code_gen.asend(None)

    async def terminate(self):
        await self.executor.terminate()

    async def reset(self):
        await self.terminate()
        await self.build()
        self.executor._cmd_space = OrderedDict()

    async def run(self, code: str, language: Literal["python", "markdown"] = "python"):
        if language == "python":
            await self.build()
            # 定义正则表达式模式，匹配以 '\n    ' 开头的行
            pattern = r"^\n    "
            # 使用 re.search 检测字符串中是否包含匹配的模式
            match = re.search(pattern, code, re.MULTILINE)
            if match:
                code = textwrap.dedent(code)
            await self.code_gen.asend(code)
            res = self.executor._cmd_space[str(len(self.executor._cmd_space) - 1)]
            if res["stderr"]:
                return "\n".join(res["stdout"]) + "\n".join(res["stderr"]), False
            return "\n".join(res["stdout"]) + "\n".join(res["stderr"]), True
        else:
            print_text_live(code)
            return code, True
