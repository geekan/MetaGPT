#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : engineer.py
@Modified By: mashenquan, 2023-11-1. In accordance with Chapter 2.2.1 and 2.2.2 of RFC 116:
    1. Modify the data type of the `cause_by` value in the `Message` to a string, and utilize the new message
        distribution feature for message filtering.
    2. Consolidate message reception and processing logic within `_observe`.
    3. Fix bug: Add logic for handling asynchronous message processing when messages are not ready.
    4. Supplemented the external transmission of internal messages.
@Modified By: mashenquan, 2023-11-27.
    1. According to Section 2.2.3.1 of RFC 135, replace file data in the message with the file name.
    2. According to the design in Section 2.2.3.5.5 of RFC 135, add incremental iteration functionality.
@Modified By: mashenquan, 2023-12-5. Enhance the workflow to navigate to WriteCode or QaEngineer based on the results
    of SummarizeCode.
"""
<<<<<<< HEAD
from __future__ import annotations

import json
from collections import defaultdict
=======
import asyncio
from collections import OrderedDict
>>>>>>> send18/dev
from pathlib import Path
from typing import Set

<<<<<<< HEAD
from metagpt.actions import Action, WriteCode, WriteCodeReview, WriteTasks
from metagpt.actions.fix_bug import FixBug
from metagpt.actions.summarize_code import SummarizeCode
from metagpt.config import CONFIG
from metagpt.const import (
    CODE_SUMMARIES_FILE_REPO,
    CODE_SUMMARIES_PDF_FILE_REPO,
    SYSTEM_DESIGN_FILE_REPO,
    TASK_FILE_REPO,
)
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import (
    CodeSummarizeContext,
    CodingContext,
    Document,
    Documents,
    Message,
)
from metagpt.utils.common import any_to_name, any_to_str, any_to_str_set
=======
import aiofiles

from metagpt.actions import WriteCode, WriteCodeReview, WriteDesign, WriteTasks
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from metagpt.utils.special_tokens import FILENAME_CODE_SEP, MSG_SEP

>>>>>>> send18/dev

IS_PASS_PROMPT = """
{context}

----
Does the above log indicate anything that needs to be done?
If there are any tasks to be completed, please answer 'NO' along with the to-do list in JSON format;
otherwise, answer 'YES' in JSON format.
"""


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
    """

<<<<<<< HEAD
    def __init__(
        self,
        name: str = "Alex",
        profile: str = "Engineer",
        goal: str = "Write elegant, readable, extensible, efficient code",
        constraints: str = "The code should conform to standards like PEP8 and be modular and maintainable",
        n_borg: int = 1,
        use_code_review: bool = False,
    ) -> None:
        """Initializes the Engineer role with given attributes."""
=======
class Engineer(Role):
    def __init__(
        self,
        name="Alex",
        profile="Engineer",
        goal="Write elegant, readable, extensible, efficient code",
        constraints="The code you write should conform to code standard like PEP8, be modular, easy to read and maintain",
        n_borg=1,
        use_code_review=False,
    ):
>>>>>>> send18/dev
        super().__init__(name, profile, goal, constraints)
        self.use_code_review = use_code_review
        self._watch([WriteTasks, SummarizeCode, WriteCode, WriteCodeReview, FixBug])
        self.code_todos = []
        self.summarize_todos = []
        self.n_borg = n_borg
        self._next_todo = any_to_name(WriteCode)

    @staticmethod
    def _parse_tasks(task_msg: Document) -> list[str]:
        m = json.loads(task_msg.content)
        return m.get("Task list")

<<<<<<< HEAD
    async def _act_sp_with_cr(self, review=False) -> Set[str]:
        changed_files = set()
        src_file_repo = CONFIG.git_repo.new_file_repository(CONFIG.src_workspace)
        for todo in self.code_todos:
            """
            # Select essential information from the historical data to reduce the length of the prompt (summarized from human experience):
            1. All from Architect
            2. All from ProjectManager
            3. Do we need other codes (currently needed)?
            TODO: The goal is not to need it. After clear task decomposition, based on the design idea, you should be able to write a single file without needing other codes. If you can't, it means you need a clearer definition. This is the key to writing longer code.
            """
            coding_context = await todo.run()
            # Code review
            if review:
                coding_context = await WriteCodeReview(context=coding_context, llm=self._llm).run()
            await src_file_repo.save(
                coding_context.filename,
                dependencies={coding_context.design_doc.root_relative_path, coding_context.task_doc.root_relative_path},
                content=coding_context.code_doc.content,
            )
            msg = Message(
                content=coding_context.json(), instruct_content=coding_context, role=self.profile, cause_by=WriteCode
            )
=======
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
            return system_design_msg.instruct_content.dict().get("Python package name").strip().strip("'").strip('"')
        return CodeParser.parse_str(block="Python package name", text=system_design_msg.content)

    def get_workspace(self) -> Path:
        msg = self._rc.memory.get_by_action(WriteDesign)[-1]
        if not msg:
            return CONFIG.workspace / "src"
        workspace = self.parse_workspace(msg)
        # Codes are written in workspace/{package_name}/{package_name}
        return CONFIG.workspace / workspace

    async def write_file(self, filename: str, code: str):
        workspace = self.get_workspace()
        filename = filename.replace('"', "").replace("\n", "")
        file = workspace / filename
        file.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file, "w") as f:
            await f.write(code)
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
        instruct_content = {}
        for todo in self.todos:
            code = await WriteCode().run(context=self._rc.history, filename=todo)
            # logger.info(todo)
            # logger.info(code_rsp)
            # code = self.parse_code(code_rsp)
            file_path = await self.write_file(todo, code)
            msg = Message(content=code, role=self.profile, cause_by=type(self._rc.todo))
>>>>>>> send18/dev
            self._rc.memory.add(msg)
            instruct_content[todo] = code

<<<<<<< HEAD
            changed_files.add(coding_context.code_doc.filename)
        if not changed_files:
            logger.info("Nothing has changed.")
        return changed_files

    async def _act(self) -> Message | None:
        """Determines the mode of action based on whether code review is used."""
        if self._rc.todo is None:
            return None
        if isinstance(self._rc.todo, WriteCode):
            self._next_todo = any_to_name(SummarizeCode)
            return await self._act_write_code()
        if isinstance(self._rc.todo, SummarizeCode):
            self._next_todo = any_to_name(WriteCode)
            return await self._act_summarize()
        return None

    async def _act_write_code(self):
        changed_files = await self._act_sp_with_cr(review=self.use_code_review)
        return Message(
            content="\n".join(changed_files),
            role=self.profile,
            cause_by=WriteCodeReview if self.use_code_review else WriteCode,
            send_to=self,
            sent_from=self,
=======
            # code_msg = todo + FILENAME_CODE_SEP + str(file_path)
            code_msg = (todo, file_path)
            code_msg_all.append(code_msg)

        logger.info(f"Done {self.get_workspace()} generating.")
        msg = Message(
            content=MSG_SEP.join(todo + FILENAME_CODE_SEP + str(file_path) for todo, file_path in code_msg_all),
            instruct_content=instruct_content,
            role=self.profile,
            cause_by=type(self._rc.todo),
            send_to="QaEngineer",
>>>>>>> send18/dev
        )

<<<<<<< HEAD
    async def _act_summarize(self):
        code_summaries_file_repo = CONFIG.git_repo.new_file_repository(CODE_SUMMARIES_FILE_REPO)
        code_summaries_pdf_file_repo = CONFIG.git_repo.new_file_repository(CODE_SUMMARIES_PDF_FILE_REPO)
        tasks = []
        src_relative_path = CONFIG.src_workspace.relative_to(CONFIG.git_repo.workdir)
        for todo in self.summarize_todos:
            summary = await todo.run()
            summary_filename = Path(todo.context.design_filename).with_suffix(".md").name
            dependencies = {todo.context.design_filename, todo.context.task_filename}
            for filename in todo.context.codes_filenames:
                rpath = src_relative_path / filename
                dependencies.add(str(rpath))
            await code_summaries_pdf_file_repo.save(
                filename=summary_filename, content=summary, dependencies=dependencies
            )
            is_pass, reason = await self._is_pass(summary)
            if not is_pass:
                todo.context.reason = reason
                tasks.append(todo.context.dict())
                await code_summaries_file_repo.save(
                    filename=Path(todo.context.design_filename).name,
                    content=todo.context.json(),
                    dependencies=dependencies,
                )
            else:
                await code_summaries_file_repo.delete(filename=Path(todo.context.design_filename).name)

        logger.info(f"--max-auto-summarize-code={CONFIG.max_auto_summarize_code}")
        if not tasks or CONFIG.max_auto_summarize_code == 0:
            return Message(
                content="",
                role=self.profile,
                cause_by=SummarizeCode,
                sent_from=self,
                send_to="Edward",  # The name of QaEngineer
            )
        # The maximum number of times the 'SummarizeCode' action is automatically invoked, with -1 indicating unlimited.
        # This parameter is used for debugging the workflow.
        CONFIG.max_auto_summarize_code -= 1 if CONFIG.max_auto_summarize_code > 0 else 0
        return Message(
            content=json.dumps(tasks), role=self.profile, cause_by=SummarizeCode, send_to=self, sent_from=self
        )

    async def _is_pass(self, summary) -> (str, str):
        rsp = await self._llm.aask(msg=IS_PASS_PROMPT.format(context=summary), stream=False)
        logger.info(rsp)
        if "YES" in rsp:
            return True, rsp
        return False, rsp

    async def _think(self) -> Action | None:
        if not CONFIG.src_workspace:
            CONFIG.src_workspace = CONFIG.git_repo.workdir / CONFIG.git_repo.workdir.name
        write_code_filters = any_to_str_set([WriteTasks, SummarizeCode, FixBug])
        summarize_code_filters = any_to_str_set([WriteCode, WriteCodeReview])
        if not self._rc.news:
            return None
        msg = self._rc.news[0]
        if msg.cause_by in write_code_filters:
            logger.info(f"TODO WriteCode:{msg.json()}")
            await self._new_code_actions(bug_fix=msg.cause_by == any_to_str(FixBug))
            return self._rc.todo
        if msg.cause_by in summarize_code_filters and msg.sent_from == any_to_str(self):
            logger.info(f"TODO SummarizeCode:{msg.json()}")
            await self._new_summarize_actions()
            return self._rc.todo
        return None

    @staticmethod
    async def _new_coding_context(
        filename, src_file_repo, task_file_repo, design_file_repo, dependency
    ) -> CodingContext:
        old_code_doc = await src_file_repo.get(filename)
        if not old_code_doc:
            old_code_doc = Document(root_path=str(src_file_repo.root_path), filename=filename, content="")
        dependencies = {Path(i) for i in await dependency.get(old_code_doc.root_relative_path)}
        task_doc = None
        design_doc = None
        for i in dependencies:
            if str(i.parent) == TASK_FILE_REPO:
                task_doc = await task_file_repo.get(i.name)
            elif str(i.parent) == SYSTEM_DESIGN_FILE_REPO:
                design_doc = await design_file_repo.get(i.name)
        context = CodingContext(filename=filename, design_doc=design_doc, task_doc=task_doc, code_doc=old_code_doc)
        return context

    @staticmethod
    async def _new_coding_doc(filename, src_file_repo, task_file_repo, design_file_repo, dependency):
        context = await Engineer._new_coding_context(
            filename, src_file_repo, task_file_repo, design_file_repo, dependency
=======
    async def _act_sp_precision(self) -> Message:
        code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
        instruct_content = {}
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
            code = await WriteCode().run(context=context_str, filename=todo)
            # code review
            if self.use_code_review:
                try:
                    rewrite_code = await WriteCodeReview().run(context=context_str, code=code, filename=todo)
                    code = rewrite_code
                except Exception as e:
                    logger.error("code review failed!", e)
                    pass
            file_path = await self.write_file(todo, code)
            msg = Message(content=code, role=self.profile, cause_by=WriteCode)
            self._rc.memory.add(msg)
            instruct_content[todo] = code

            code_msg = (todo, file_path)
            code_msg_all.append(code_msg)

        logger.info(f"Done {self.get_workspace()} generating.")
        msg = Message(
            content=MSG_SEP.join(todo + FILENAME_CODE_SEP + str(file_path) for todo, file_path in code_msg_all),
            instruct_content=instruct_content,
            role=self.profile,
            cause_by=type(self._rc.todo),
            send_to="QaEngineer",
>>>>>>> send18/dev
        )
        coding_doc = Document(root_path=str(src_file_repo.root_path), filename=filename, content=context.json())
        return coding_doc

    async def _new_code_actions(self, bug_fix=False):
        # Prepare file repos
        src_file_repo = CONFIG.git_repo.new_file_repository(CONFIG.src_workspace)
        changed_src_files = src_file_repo.all_files if bug_fix else src_file_repo.changed_files
        task_file_repo = CONFIG.git_repo.new_file_repository(TASK_FILE_REPO)
        changed_task_files = task_file_repo.changed_files
        design_file_repo = CONFIG.git_repo.new_file_repository(SYSTEM_DESIGN_FILE_REPO)

        changed_files = Documents()
        # Recode caused by upstream changes.
        for filename in changed_task_files:
            design_doc = await design_file_repo.get(filename)
            task_doc = await task_file_repo.get(filename)
            task_list = self._parse_tasks(task_doc)
            for task_filename in task_list:
                old_code_doc = await src_file_repo.get(task_filename)
                if not old_code_doc:
                    old_code_doc = Document(root_path=str(src_file_repo.root_path), filename=task_filename, content="")
                context = CodingContext(
                    filename=task_filename, design_doc=design_doc, task_doc=task_doc, code_doc=old_code_doc
                )
                coding_doc = Document(
                    root_path=str(src_file_repo.root_path), filename=task_filename, content=context.json()
                )
                if task_filename in changed_files.docs:
                    logger.warning(
                        f"Log to expose potential conflicts: {coding_doc.json()} & "
                        f"{changed_files.docs[task_filename].json()}"
                    )
                changed_files.docs[task_filename] = coding_doc
        self.code_todos = [WriteCode(context=i, llm=self._llm) for i in changed_files.docs.values()]
        # Code directly modified by the user.
        dependency = await CONFIG.git_repo.get_dependency()
        for filename in changed_src_files:
            if filename in changed_files.docs:
                continue
            coding_doc = await self._new_coding_doc(
                filename=filename,
                src_file_repo=src_file_repo,
                task_file_repo=task_file_repo,
                design_file_repo=design_file_repo,
                dependency=dependency,
            )
            changed_files.docs[filename] = coding_doc
            self.code_todos.append(WriteCode(context=coding_doc, llm=self._llm))

        if self.code_todos:
            self._rc.todo = self.code_todos[0]

    async def _new_summarize_actions(self):
        src_file_repo = CONFIG.git_repo.new_file_repository(CONFIG.src_workspace)
        src_files = src_file_repo.all_files
        # Generate a SummarizeCode action for each pair of (system_design_doc, task_doc).
        summarizations = defaultdict(list)
        for filename in src_files:
            dependencies = await src_file_repo.get_dependency(filename=filename)
            ctx = CodeSummarizeContext.loads(filenames=dependencies)
            summarizations[ctx].append(filename)
        for ctx, filenames in summarizations.items():
            ctx.codes_filenames = filenames
            self.summarize_todos.append(SummarizeCode(context=ctx, llm=self._llm))
        if self.summarize_todos:
            self._rc.todo = self.summarize_todos[0]

    @property
    def todo(self) -> str:
        return self._next_todo
