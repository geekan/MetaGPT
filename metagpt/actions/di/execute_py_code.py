# -*- encoding: utf-8 -*-
"""
@Date    :   2024/11/14 22:48:29
@Author  :   orange-crow
@File    :   execute_py_code.py
"""

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

    async def run(self, code: str, language: Literal["python", "markdown"] = "python"):
        if language == "python":
            await self.build()
            await self.code_gen.asend(code)
            res = self.executor._cmd_space[str(len(self.executor._cmd_space) - 1)]
            if res["stderr"]:
                return res["stderr"], False
            return res["stdout"], True
        else:
            print_text_live(code)
            return code, True
