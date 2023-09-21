#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/12 14:50
@Author  : femto Zheng
@File    : write_many_codes.py
"""
from pathlib import Path

from metagpt.actions import Action, WriteCode, WriteCodeReview, WriteDesign, WriteTasks
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from metagpt.utils.special_tokens import FILENAME_CODE_SEP, MSG_SEP


class WriteManyCodes(Action):
    def __init__(self, name="WriteCode", context: list[Message] = None, llm=None, role=None):
        super().__init__(name, context, llm)
        self.role = role

    def parse_tasks(self, task_msg: Message) -> list[str]:
        if task_msg.instruct_content:
            return task_msg.instruct_content.dict().get("Task list")
        return CodeParser.parse_file_list(block="Task list", text=task_msg.content)

    def parse_code(self, code_text: str) -> str:
        return CodeParser.parse_code(block="", text=code_text)

    def parse_workspace(self, system_design_msg: Message) -> str:
        if system_design_msg.instruct_content:
            return system_design_msg.instruct_content.dict().get("Python package name").strip().strip("'").strip('"')
        return CodeParser.parse_str(block="Python package name", text=system_design_msg.content)

    def get_workspace(self) -> Path:
        msg = self.role._rc.memory.get_by_action(WriteDesign)[-1]
        if not msg:
            return WORKSPACE_ROOT / "src"
        workspace = self.parse_workspace(msg)
        # Codes are written in workspace/{package_name}/{package_name}
        return WORKSPACE_ROOT / workspace / workspace

    # this isn't used? so I comment out
    # def recreate_workspace(self):
    #     workspace = self.get_workspace()
    #     try:
    #         shutil.rmtree(workspace)
    #     except FileNotFoundError:
    #         pass  # The folder does not exist, but we don't care
    #     workspace.mkdir(parents=True, exist_ok=True)

    def write_file(self, filename: str, code: str):
        workspace = self.get_workspace()
        filename = filename.replace('"', "").replace("\n", "")
        file = workspace / filename
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(code)
        return file

    def _is_invalid(self, filename):
        return any(i in filename for i in ["mp3", "wav"])

    # async def gather_ordered_k(coros, k) -> list:
    #     tasks = OrderedDict()
    #     results = [None] * len(coros)
    #     done_queue = asyncio.Queue()
    #
    #     for i, coro in enumerate(coros):
    #         if len(tasks) >= k:
    #             done, _ = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
    #             for task in done:
    #                 index = tasks.pop(task)
    #                 await done_queue.put((index, task.result()))
    #         task = asyncio.create_task(coro)
    #         tasks[task] = i
    #
    #     if tasks:
    #         done, _ = await asyncio.wait(tasks.keys())
    #         for task in done:
    #             index = tasks[task]
    #             await done_queue.put((index, task.result()))
    #
    #     while not done_queue.empty():
    #         index, result = await done_queue.get()
    #         results[index] = result
    #
    #     return results

    # do we still need this function here?
    async def _run_sp(self) -> Message:
        code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
        for todo in self.todos:
            code = await WriteCode().run(context=self.role._rc.history, filename=todo)
            # logger.info(todo)
            # logger.info(code_rsp)
            # code = self.parse_code(code_rsp)
            file_path = self.write_file(todo, code)
            msg = Message(content=code, role=self.profile, cause_by=type(self._rc.todo))
            self.role._rc.memory.add(msg)

            code_msg = todo + FILENAME_CODE_SEP + str(file_path)
            code_msg_all.append(code_msg)

        logger.info(f"Done {self.get_workspace()} generating.")
        msg = Message(
            content=MSG_SEP.join(code_msg_all), role=self.role.profile, cause_by=WriteCode, send_to="QaEngineer"
        )
        return msg

    async def _run_sp_precision(self) -> Message:
        code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
        for todo in self.todos:
            """
            # Select essential information from the historical data to reduce the length of the prompt (summarized from human experience):
            1. All from Architect
            2. All from ProjectManager
            3. Do we need other codes (currently needed)?
            TODO: The goal is not to need it. After clear task decomposition, based on the design idea, you should be able to write a single file without needing other codes. If you can't, it means you need a clearer definition. This is the key to writing longer code.
            """
            context = []
            msg = self.role._rc.memory.get_by_actions([WriteDesign, WriteTasks, WriteCode])
            for m in msg:
                context.append(m.content)
            context_str = "\n".join(context)
            # Write code
            code = await WriteCode().run(context=context_str, filename=todo)
            # Code review
            if self.role.use_code_review:
                try:
                    rewrite_code = await WriteCodeReview().run(context=context_str, code=code, filename=todo)
                    code = rewrite_code
                except Exception as e:
                    logger.error("code review failed!", e)
                    pass
            file_path = self.write_file(todo, code)
            msg = Message(content=code, role=self.profile, cause_by=WriteCode)
            self.role._rc.memory.add(msg)

            code_msg = todo + FILENAME_CODE_SEP + str(file_path)
            code_msg_all.append(code_msg)

        logger.info(f"Done {self.get_workspace()} generating.")
        msg = Message(
            content=MSG_SEP.join(code_msg_all),
            role=self.role.profile,
            cause_by=WriteCodeReview
            if self.role.use_code_review
            else WriteCode,  # probably should just be WriteManyCode and let QaEngineer Watch WriteManyCode
            send_to="QaEngineer",
        )
        return msg

    async def run(self, context):
        """Determines the mode of action based on whether code review is used."""
        self.todos = self.parse_tasks(context[-1])
        # if self.role.use_code_review:
        return (
            await self._run_sp_precision()
        )  # I see _run_sp_precision already handle if code review or not, so I don't use _run_sp
        # return await self._run_sp()
