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


async def gather_ordered_k(coros, k) -> list:
    """Execute coroutines in order and gather results for up to k coroutines at once."""
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
                 constraints="The code you write should conform to code standards like PEP8, be modular, easy to read and maintain",
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
        """Extract tasks from a message."""
        if not task_msg.instruct_content:
            return task_msg.instruct_content.dict().get("Task list")
        return CodeParser.parse_file_list(block="Task list", text=task_msg.content)

    @classmethod
    def parse_code(self, code_text: str) -> str:
        """Extract code from a given text."""
        return CodeParser.parse_code(block="", text=code_text)

    @classmethod
    def parse_workspace(cls, system_design_msg: Message) -> str:
        """Extract workspace name from a system design message."""
        if not system_design_msg.instruct_content:
            return system_design_msg.instruct_content.dict().get("Python package name")
        return CodeParser.parse_str(block="Python package name", text=system_design_msg.content)

    def get_workspace(self) -> Path:
        """Determine the directory where the code will be written."""
        msg = self._rc.memory.get_by_action(WriteDesign)[-1]
        if not msg:
            return WORKSPACE_ROOT / 'src'
        workspace = self.parse_workspace(msg)
        # Codes are written in workspace/{package_name}/{package_name}
        return WORKSPACE_ROOT / workspace / workspace

    def recreate_workspace(self):
        """Remove and recreate the workspace directory."""
        workspace = self.get_workspace()
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass  # Directory doesn't exist, but we don't mind
        workspace.mkdir(parents=True, exist_ok=True)

    def write_file(self, filename: str, code: str):
        """Write code to a specified file."""
        workspace = self.get_workspace()
        file = workspace / filename
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(code)

    def recv(self, message: Message) -> None:
        """Receive a message and process it."""
        self._rc.memory.add(message)
        if message in self._rc.important_memory:
            self.todos = self.parse_tasks(message)

    async def _act_mp(self) -> Message:
        """Act in a multi-process manner."""
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
            msg = Message(content=code_rsp, role=self.profile, cause_by=type(self._rc.todo))
            self._rc.memory.add(msg)
            del self.todos[0]

        logger.info(f'Finished generating in {self.get_workspace()} directory.')
        msg = Message(content="all done.", role=self.profile, cause_by=type(self._rc.todo))
        return msg

    async def _act_sp(self) -> Message:
        """Act in a single-process manner."""
        for todo in self.todos:
            code_rsp = await WriteCode().run(
                context=self._rc.history,
                filename=todo
            )
            self.write_file(todo, code_rsp)
            msg = Message(content=code_rsp, role=self.profile, cause_by=type(self._rc.todo))
            self._rc.memory.add(msg)

        logger.info(f'Finished generating in {self.get_workspace()} directory.')
        msg = Message(content="all done.", role=self.profile, cause_by=type(self._rc.todo))
        return msg

    async def _act_sp_precision(self) -> Message:
        """Using precision approach to perform actions based on available tasks."""
        for todo in self.todos:
            """
            # From the historical information, select the necessary information to reduce the prompt length (summarized from human experience):
            1. All from Architect
            2. All from ProjectManager
            3. Is other code needed (temporarily needed)?
            TODO: The goal is not to need it. Once tasks are clearly broken down and based on design logic, there shouldn't be a need for other codes to clearly write a single file. If not possible, it indicates that clearer definitions are still needed. This is key to writing extensive code.
            """
            context = []
            # Retrieve messages related to design, tasks, and code writing from memory.
            msg = self._rc.memory.get_by_actions([WriteDesign, WriteTasks, WriteCode])
            for m in msg:
                context.append(m.content)
            context_str = "\n".join(context)
            
            # Write code based on the given context and task.
            code = await WriteCode().run(
                context=context_str,
                filename=todo
            )
            
            # If code review is enabled, review and potentially rewrite the code.
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
            
            # Save the written code to a file.
            self.write_file(todo, code)
            
            # Add the written code message to memory.
            msg = Message(content=code, role=self.profile, cause_by=WriteCode)
            self._rc.memory.add(msg)

        logger.info(f'Code generation completed for workspace: {self.get_workspace()}.')
        msg = Message(content="all done.", role=self.profile, cause_by=WriteCode)
        return msg

    async def _act(self) -> Message:
        """Determine the appropriate method for action and execute it."""
        if self.use_code_review:
            return await self._act_sp_precision()
        return await self._act_sp()

