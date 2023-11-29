#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : engineer.py
"""
import asyncio
import re
import shutil
from collections import OrderedDict
from pathlib import Path
from typing import List

from metagpt.actions import WriteCode, WriteCodeReview, WriteDesign, WriteTasks, BossRequirement
from metagpt.actions.refine_design_api import RefineDesign
from metagpt.actions.refine_prd import RefinePRD
from metagpt.actions.refine_project_management import RefineTasks
from metagpt.actions.write_code_refine import WriteCodeRefine
from metagpt.actions.write_code_guide import WriteCodeGuide
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from metagpt.utils.special_tokens import FILENAME_CODE_SEP, MSG_SEP


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
    """
    Represents an Engineer role responsible for writing and possibly reviewing code.

    Attributes:
        name (str): Name of the engineer.
        profile (str): Role profile, default is 'Engineer'.
        goal (str): Goal of the engineer.
        constraints (str): Constraints for the engineer.
        n_borg (int): Number of borgs.
        use_code_review (bool): Whether to use code review.
        todos (list): List of tasks.
    """

    def __init__(
        self,
        name: str = "Alex",
        profile: str = "Engineer",
        goal: str = "Write elegant, readable, extensible, efficient code",
        constraints: str = "The code should conform to standards like PEP8 and be modular and maintainable",
        n_borg: int = 1,
        use_code_review: bool = False,
        increment: bool = False,
        bug_fix: bool = False,
    ) -> None:
        """Initializes the Engineer role with given attributes."""
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WriteCode])
        self.use_code_review = use_code_review
        self.increment = increment
        self.bug_fix = bug_fix
        if self.use_code_review:
            self._init_actions([WriteCode, WriteCodeReview])

        if self.increment:
            self._init_actions([WriteCodeGuide, WriteCodeRefine, WriteCodeReview])
            self._watch([RefineTasks])
        else:
            self._watch([WriteTasks])

        self.todos = []
        self.n_borg = n_borg

    @classmethod
    def parse_tasks(self, task_msg: Message) -> list[str]:
        if task_msg.instruct_content:
            return task_msg.instruct_content.dict().get("Task list")
        return CodeParser.parse_file_list(block="Task list", text=task_msg.content)

    @classmethod
    def parse_todos(self, bug_context: List) -> list[str]:
        for msg in bug_context:
            if msg.sent_from == "ProjectManager":
                content = msg.content
                tasks_section = re.search(r"## Task list\n\n(.*?)(\n\n|$)", content, re.DOTALL)
                if tasks_section:
                    tasks = tasks_section.group(1).split("\n")
                    tasks = [task.strip("-").strip() for task in tasks]
                    return tasks
                return []

    @classmethod
    def parse_code(self, code_text: str) -> str:
        return CodeParser.parse_code(block="", text=code_text)

    @classmethod
    def parse_workspace(cls, system_design_msg: Message) -> str:
        if system_design_msg.instruct_content:
            return system_design_msg.instruct_content.dict().get("Python package name").strip().strip("'").strip('"')
        return CodeParser.parse_str(block="Python package name", text=system_design_msg.content)

    def get_workspace(self) -> Path:
        if self.increment:
            msg = self._rc.memory.get_by_action(RefineDesign)[-1]
        elif self.bug_fix:
            msg = self._rc.memory.get_by_action(BossRequirement)[-1]
        else:
            msg = self._rc.memory.get_by_action(WriteDesign)[-1]
        if not msg:
            return WORKSPACE_ROOT / "src"
        workspace = self.parse_workspace(msg)
        workspace = workspace if workspace else "src"
        # Codes are written in workspace/{package_name}/{package_name}
        return WORKSPACE_ROOT / workspace / workspace
        # return self.create_or_increment_workspace(WORKSPACE_ROOT, workspace)

    def recreate_workspace(self):
        workspace = self.get_workspace()
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass  # The folder does not exist, but we don't care
        workspace.mkdir(parents=True, exist_ok=True)

    def write_file(self, workspace: Path, filename: str, code: str) -> Path:
        filename = filename.replace('"', "").replace("\n", "")
        file = workspace / filename
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(code)
        return file

    def recv(self, message: Message) -> None:
        self._rc.memory.add(message)
        if message in self._rc.important_memory:
            if not self.bug_fix:
                self.todos = self.parse_tasks(message)
            else:
                self.todos = self.parse_todos(self.bug_msgs)

    async def _act_mp(self) -> Message:
        # self.recreate_workspace()
        todo_coros = []
        for todo in self.todos:
            todo_coro = WriteCode().run(
                context=self._rc.memory.get_by_actions([WriteTasks, WriteDesign]), filename=todo
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

        logger.info(f"Done {self.get_workspace()} generating.")
        msg = Message(content="all done.", role=self.profile, cause_by=type(self._rc.todo))
        return msg

    async def _act_sp(self) -> Message:
        code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
        workspace = self.get_workspace()
        for todo in self.todos:
            code = await WriteCode().run(context=self._rc.history, filename=todo)
            # logger.info(todo)
            # logger.info(code_rsp)
            # code = self.parse_code(code_rsp)
            file_path = self.write_file(workspace, todo, code)
            msg = Message(content=code, role=self.profile, cause_by=type(self._rc.todo))
            self._rc.memory.add(msg)

            code_msg = todo + FILENAME_CODE_SEP + str(file_path)
            code_msg_all.append(code_msg)

        logger.info(f"Done {self.get_workspace()} generating.")
        msg = Message(
            content=MSG_SEP.join(code_msg_all), role=self.profile, cause_by=type(self._rc.todo), send_to="QaEngineer"
        )
        return msg

    async def _act_increment(self) -> Message:
        code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
        workspace = self.get_workspace()
        # human_str = "\n".join([msg.content for msg in self._rc.memory.get_by_role("Human")])
        human_str = str(self._rc.memory.get_by_role("Human")[0])
        code = self._rc.env.get_legacy()["legacy_code"]

        # Refine code
        context = []
        msg = self._rc.memory.get_by_actions([RefinePRD, RefineDesign, RefineTasks])

        for m in msg:
            context.append(m.content)
        context_str = human_str + "\n".join(context)
        try:
            logger.info("Write Code Guide start!")
            guide = await WriteCodeGuide().run(context=context_str, code=code)
            msg = Message(content=guide, role=self.profile, cause_by=WriteCodeGuide)
            self._rc.memory.add(msg)
        except Exception as e:
            logger.error("Write Code Guide failed!", e)
            pass

        # Write code or Code review
        for todo in self.todos:
            msg = self._rc.memory.get_by_actions([RefineTasks])
            context_str = human_str + "\n".join([m.content for m in msg])
            # WriteCodeRefine
            try:
                logger.info("Write Code Refine start!")
                code = await WriteCodeRefine().run(context=context_str, code=code, filename=todo, guide=guide)
            except Exception as e:
                logger.error("Write Code Refine failed!", e)
                pass
            # FIXME: Code review Action
            # if self.use_code_review:
            #     try:
            #         rewrite_code = await WriteCodeReview().run(context=context_str, code=code, filename=todo)
            #         code = rewrite_code
            #     except Exception as e:
            #         logger.error("code review failed!", e)
            #         pass
            file_path = self.write_file(workspace, todo, code)
            msg = Message(content=code, role=self.profile, cause_by=WriteCodeRefine)
            self._rc.memory.add(msg)

            code_msg = todo + FILENAME_CODE_SEP + str(file_path)
            code_msg_all.append(code_msg)

        logger.info(f"Done {self.get_workspace()} generating.")
        msg = Message(
            content=MSG_SEP.join(code_msg_all), role=self.profile, cause_by=type(self._rc.todo), send_to="QaEngineer"
        )
        return msg

    async def _act_bug_fix(self, bug_msgs) -> Message:
        code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
        workspace = self.get_workspace()
        flag = True
        # legacy_codes = legacy.split('---')
        for todo in self.todos:
            context = []

            for m in bug_msgs:
                if m.sent_from != "Engineer":
                    context.append(m.content)
                context.append(m.content)
            context_str = "\n".join(context)
            code = [m.content for m in bug_msgs if m.sent_from == "Engineer"]
            code = "\n".join(code)

            # Refine code or Write code
            # if self.increment and len(legacy_codes) > 0:
            #     code = legacy_codes.pop(0)

            # Code review
            try:
                rewrite_code = await WriteCodeGuide().run(context=context_str, code=code, filename=todo)
                code = rewrite_code
            except Exception as e:
                logger.error("code review failed!", e)
                pass

            # code = await WriteCode().run(context=context_str, filename=todo)

            file_path = self.write_file(workspace, todo, code)
            msg = Message(content=code, role=self.profile, cause_by=WriteCode)
            self._rc.memory.add(msg)

            code_msg = todo + FILENAME_CODE_SEP + str(file_path)
            code_msg_all.append(code_msg)

        logger.info(f"Done {self.get_workspace()} generating.")
        msg = Message(
            content=MSG_SEP.join(code_msg_all), role=self.profile, cause_by=type(self._rc.todo), send_to="QaEngineer"
        )
        return msg

    async def _act_sp_precision(self) -> Message:
        code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
        workspace = self.get_workspace()
        for todo in self.todos:
            """
            # Select essential information from the historical data to reduce the length of the prompt (summarized from human experience):
            1. All from Architect
            2. All from ProjectManager
            3. Do we need other codes (currently needed)?
            TODO: The goal is not to need it. After clear task decomposition, based on the design idea, you should be able to write a single file without needing other codes. If you can't, it means you need a clearer definition. This is the key to writing longer code.
            """
            context = []
            msg = self._rc.memory.get_by_actions([WriteDesign, WriteTasks, WriteCode])
            for m in msg:
                context.append(m.content)
            context_str = "\n".join(context)
            # Write code
            code = await WriteCode().run(context=context_str, filename=todo)
            # Code review
            if self.use_code_review:
                try:
                    rewrite_code = await WriteCodeReview().run(context=context_str, code=code, filename=todo)
                    code = rewrite_code
                except Exception as e:
                    logger.error("code review failed!", e)
                    pass
            file_path = self.write_file(workspace, todo, code)
            msg = Message(content=code, role=self.profile, cause_by=WriteCode)
            self._rc.memory.add(msg)

            code_msg = todo + FILENAME_CODE_SEP + str(file_path)
            code_msg_all.append(code_msg)

        logger.info(f"Done {self.get_workspace()} generating.")
        msg = Message(
            content=MSG_SEP.join(code_msg_all), role=self.profile, cause_by=type(self._rc.todo), send_to="QaEngineer"
        )
        return msg

    # async def _observe(self) -> int:
    #     if self.bug_fix:
    #         msg = Message(
    #             content=self.bug_msgs[0].content + "\n---\n" + self.legacy,
    #             role=self.profile,
    #             cause_by=BossRequirement,
    #             sent_from=self.profile,
    #             send_to=self.profile,
    #         )
    #         self._publish_message(msg)
    #     await super()._observe()
    #     self._rc.news = [
    #         msg for msg in self._rc.news if msg.send_to == self.profile
    #     ]  # only relevant msgs count as observed news
    #     return len(self._rc.news)

    async def _act(self) -> Message:
        """Determines the mode of action based on whether code review is used."""
        if self.increment:
            logger.info(f"{self._setting}: ready to WriteExtraCode and WriteCodeRefine")
        else:
            logger.info(f"{self._setting}: ready to WriteCode")

        if self.increment:
            return await self._act_increment()
        elif self.use_code_review:
            return await self._act_sp_precision()
        return await self._act_sp()
