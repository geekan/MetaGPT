#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : engineer.py
"""
import asyncio
import shutil
from collections import OrderedDict
from pathlib import Path

from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.actions import WriteCode, WriteCodeReview, WriteTasks, WriteDesign
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from metagpt.utils.special_tokens import MSG_SEP, FILENAME_CODE_SEP


async def gather_ordered_k(coros, k) -> list:
    tasks = OrderedDict()
    results = [None] * len(coros)
    done_queue = asyncio.Queue()

    for i, coro in enumerate(coros):
        if len(tasks) >= k:
            done, _ = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                index = tasks.pop(task)
                await done_queue.put((index, task.result()))
        task = asyncio.create_task(coro)
        tasks[task] = i

    if tasks:
        done, _ = await asyncio.wait(tasks.keys())
        for task in done:
            index = tasks[task]
            await done_queue.put((index, task.result()))

    while not done_queue.empty():
        index, result = await done_queue.get()
        results[index] = result

    return results


class Engineer(Role):
    def __init__(self, name="Alex", profile="Engineer", goal="Write elegant, readable, extensible, efficient code",
                 constraints="The code you write should conform to code standard like PEP8, be modular, easy to read and maintain",
                 n_borg=1, use_code_review=False):
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WriteCode])
        self.use_code_review = use_code_review
        if self.use_code_review:
            self._init_actions([WriteCode, WriteCodeReview])
        self._watch([WriteTasks])
        self.todos = []
        self.n_borg = n_borg

    @classmethod
    def parse_tasks(self, task_msg: Message) -> list[str]:
        if task_msg.instruct_content:
            return task_msg.instruct_content.dict().get("Task list")
        return CodeParser.parse_file_list(block="Task list", text=task_msg.content)

    @classmethod
    def parse_code(self, code_text: str) -> str:
        return CodeParser.parse_code(block="", text=code_text)

    @classmethod
    def parse_workspace(cls, system_design_msg: Message) -> str:
        if system_design_msg.instruct_content:
            return system_design_msg.instruct_content.dict().get("Python package name").strip().strip("'").strip("\"")
        return CodeParser.parse_str(block="Python package name", text=system_design_msg.content)

    def get_workspace(self) -> Path:
        msg = self._rc.memory.get_by_action(WriteDesign)[-1]
        if not msg:
            return WORKSPACE_ROOT / 'src'
        workspace = self.parse_workspace(msg)
        # Codes are written in workspace/{package_name}/{package_name}
        return WORKSPACE_ROOT / workspace / workspace

    def recreate_workspace(self):
        workspace = self.get_workspace()
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass  # 文件夹不存在，但我们不在意
        workspace.mkdir(parents=True, exist_ok=True)

    def write_file(self, filename: str, code: str):
        workspace = self.get_workspace()
        filename = filename.replace('"', '').replace('\n', '')
        file = workspace / filename
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(code)
        return file

    def recv(self, message: Message) -> None:
        self._rc.memory.add(message)
        if message in self._rc.important_memory:
            self.todos = self.parse_tasks(message)

    async def _act_mp(self) -> Message:
        # self.recreate_workspace()
        todo_coros = []
        for todo in self.todos:
            todo_coro = WriteCode().run(
                context=self._rc.memory.get_by_actions([WriteTasks, WriteDesign]),
                filename=todo
            )
            todo_coros.append(todo_coro)

        rsps = await gather_ordered_k(todo_coros, self.n_borg)
        for todo, code_rsp in zip(self.todos, rsps):
            _ = self.parse_code(code_rsp)
            logger.info(todo)
            logger.info(code_rsp)
            # self.write_file(todo, code)
            msg = Message(content=code_rsp, role=self.profile, cause_by=type(self._rc.todo))
            self._rc.memory.add(msg)
            del self.todos[0]

        logger.info(f'Done {self.get_workspace()} generating.')
        msg = Message(content="all done.", role=self.profile, cause_by=type(self._rc.todo))
        return msg

    async def _act_sp(self) -> Message:
        code_msg_all = [] # gather all code info, will pass to qa_engineer for tests later
        for todo in self.todos:
            code = await WriteCode().run(
                context=self._rc.history,
                filename=todo
            )
            # logger.info(todo)
            # logger.info(code_rsp)
            # code = self.parse_code(code_rsp)
            file_path = self.write_file(todo, code)
            msg = Message(content=code, role=self.profile, cause_by=type(self._rc.todo))
            self._rc.memory.add(msg)

            code_msg = todo + FILENAME_CODE_SEP + str(file_path)
            code_msg_all.append(code_msg)

        logger.info(f'Done {self.get_workspace()} generating.')
        msg = Message(
            content=MSG_SEP.join(code_msg_all),
            role=self.profile,
            cause_by=type(self._rc.todo),
            send_to="QaEngineer"
        )
        return msg

    async def _act_sp_precision(self) -> Message:
        code_msg_all = [] # gather all code info, will pass to qa_engineer for tests later
        for todo in self.todos:
            """
            # 从历史信息中挑选必须的信息，以减少prompt长度（人工经验总结）
            1. Architect全部
            2. ProjectManager全部
            3. 是否需要其他代码（暂时需要）？
            TODO:目标是不需要。在任务拆分清楚后，根据设计思路，不需要其他代码也能够写清楚单个文件，如果不能则表示还需要在定义的更清晰，这个是代码能够写长的关键
            """
            context = []
            msg = self._rc.memory.get_by_actions([WriteDesign, WriteTasks, WriteCode])
            for m in msg:
                context.append(m.content)
            context_str = "\n".join(context)
            # 编写code
            code = await WriteCode().run(
                context=context_str,
                filename=todo
            )
            # code review
            if self.use_code_review:
                try:
                    rewrite_code = await WriteCodeReview().run(
                        context=context_str,
                        code=code,
                        filename=todo
                    )
                    code = rewrite_code
                except Exception as e:
                    logger.error("code review failed!", e)
                    pass
            file_path = self.write_file(todo, code)
            msg = Message(content=code, role=self.profile, cause_by=WriteCode)
            self._rc.memory.add(msg)

            code_msg = todo + FILENAME_CODE_SEP + str(file_path)
            code_msg_all.append(code_msg)

        logger.info(f'Done {self.get_workspace()} generating.')
        msg = Message(
            content=MSG_SEP.join(code_msg_all),
            role=self.profile,
            cause_by=type(self._rc.todo),
            send_to="QaEngineer"
        )
        return msg

    async def _act(self) -> Message:
        if self.use_code_review:
            return await self._act_sp_precision()
        return await self._act_sp()
