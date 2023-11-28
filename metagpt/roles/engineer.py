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
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Set

from metagpt.actions import Action, WriteCode, WriteCodeReview, WriteTasks
from metagpt.actions.summarize_code import SummarizeCode
from metagpt.config import CONFIG
from metagpt.const import MESSAGE_ROUTE_TO_NONE, SYSTEM_DESIGN_FILE_REPO, TASK_FILE_REPO
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import (
    CodeSummarizeContext,
    CodingContext,
    Document,
    Documents,
    Message,
)


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
        super().__init__(name, profile, goal, constraints)
        self.use_code_review = use_code_review
        self._watch([WriteTasks])
        self.code_todos = []
        self.summarize_todos = []
        self.n_borg = n_borg

    @staticmethod
    def _parse_tasks(task_msg: Document) -> list[str]:
        m = json.loads(task_msg.content)
        return m.get("Task list")

    # @classmethod
    # def parse_tasks(cls, task_msg: Message) -> list[str]:
    #     if task_msg.instruct_content:
    #         return task_msg.instruct_content.dict().get("Task list")
    #     return CodeParser.parse_file_list(block="Task list", text=task_msg.content)
    #
    # @classmethod
    # def parse_code(cls, code_text: str) -> str:
    #     return CodeParser.parse_code(block="", text=code_text)
    #
    # @classmethod
    # def parse_workspace(cls, system_design_msg: Message) -> str:
    #     if system_design_msg.instruct_content:
    #         return system_design_msg.instruct_content.dict().get("project_name").strip().strip("'").strip('"')
    #     return CodeParser.parse_str(block="project_name", text=system_design_msg.content)
    #
    # def get_workspace(self) -> Path:
    #     msg = self._rc.memory.get_by_action(WriteDesign)[-1]
    #     if not msg:
    #         return CONFIG.workspace_path / "src"
    #     workspace = self.parse_workspace(msg)
    #     # Codes are written in workspace/{package_name}/{package_name}
    #     return CONFIG.workspace_path / workspace / workspace
    #
    # def recreate_workspace(self):
    #     workspace = self.get_workspace()
    #     try:
    #         shutil.rmtree(workspace)
    #     except FileNotFoundError:
    #         pass  # The folder does not exist, but we don't care
    #     workspace.mkdir(parents=True, exist_ok=True)
    #
    # def write_file(self, filename: str, code: str):
    #     workspace = self.get_workspace()
    #     filename = filename.replace('"', "").replace("\n", "")
    #     file = workspace / filename
    #     file.parent.mkdir(parents=True, exist_ok=True)
    #     file.write_text(code)
    #     return file
    #
    # def recv(self, message: Message) -> None:
    #     self._rc.memory.add(message)
    #     if message in self._rc.important_memory:
    #         self.todos = self.parse_tasks(message)
    #
    # async def _act_mp(self) -> Message:
    #     # self.recreate_workspace()
    #     todo_coros = []
    #     for todo in self.todos:
    #         todo_coro = WriteCode().run(
    #             context=self._rc.memory.get_by_actions([WriteTasks, WriteDesign]), filename=todo
    #         )
    #         todo_coros.append(todo_coro)
    #
    #     rsps = await gather_ordered_k(todo_coros, self.n_borg)
    #     for todo, code_rsp in zip(self.todos, rsps):
    #         _ = self.parse_code(code_rsp)
    #         logger.info(todo)
    #         logger.info(code_rsp)
    #         # self.write_file(todo, code)
    #         msg = Message(content=code_rsp, role=self.profile, cause_by=type(self._rc.todo))
    #         self._rc.memory.add(msg)
    #         del self.todos[0]
    #
    #     logger.info(f"Done {self.get_workspace()} generating.")
    #     msg = Message(content="all done.", role=self.profile, cause_by=type(self._rc.todo))
    #     return msg
    #
    # async def _act_sp(self) -> Message:
    #     code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
    #     for todo in self.todos:
    #         code = await WriteCode().run(context=self._rc.history, filename=todo)
    #         # logger.info(todo)
    #         # logger.info(code_rsp)
    #         # code = self.parse_code(code_rsp)
    #         file_path = self.write_file(todo, code)
    #         msg = Message(content=code, role=self.profile, cause_by=type(self._rc.todo))
    #         self._rc.memory.add(msg)
    #
    #         code_msg = todo + FILENAME_CODE_SEP + str(file_path)
    #         code_msg_all.append(code_msg)
    #
    #     logger.info(f"Done {self.get_workspace()} generating.")
    #     msg = Message(
    #         content=MSG_SEP.join(code_msg_all), role=self.profile, cause_by=type(self._rc.todo), send_to="QaEngineer"
    #     )
    #     return msg

    # async def _act_sp_with_cr(self) -> Message:
    #     code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
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
            # =======
            #             context = []
            #             msg = self._rc.memory.get_by_actions([WriteDesign, WriteTasks, WriteCode])
            #             for m in msg:
            #                 context.append(m.content)
            #             context_str = "\n----------\n".join(context)
            #             # Write code
            #             code = await WriteCode().run(context=context_str, filename=todo)
            #             # Code review
            #             if self.use_code_review:
            #                 # try:
            #                 rewrite_code = await WriteCodeReview().run(context=context_str, code=code, filename=todo)
            #                 code = rewrite_code
            #                 # except Exception as e:
            #                 #     logger.error("code review failed!", e)
            #             file_path = self.write_file(todo, code)
            #             msg = Message(content=code, role=self.profile, cause_by=WriteCode)
            # >>>>>>> feature/geekan_cli_etc
            self._rc.memory.add(msg)

            changed_files.add(coding_context.code_doc.filename)
        if not changed_files:
            logger.info("Nothing has changed.")
        return changed_files

    async def _act(self) -> Message | None:
        """Determines the mode of action based on whether code review is used."""
        if self._rc.todo is None:
            return None
        if isinstance(self._rc.todo, WriteCode):
            changed_files = await self._act_sp_with_cr(review=self.use_code_review)
            # Unit tests only.
            if CONFIG.REQA_FILENAME and CONFIG.REQA_FILENAME not in changed_files:
                changed_files.add(CONFIG.REQA_FILENAME)
            return Message(
                content="\n".join(changed_files),
                role=self.profile,
                cause_by=WriteCodeReview if self.use_code_review else WriteCode,
                send_to="Edward",  # The name of QaEngineer
            )
        if isinstance(self._rc.todo, SummarizeCode):
            summaries = []
            for todo in self.summarize_todos:
                summary = await todo.run()
                summaries.append(summary.json(ensure_ascii=False))
            return Message(
                content="\n".join(summaries),
                role=self.profile,
                cause_by=SummarizeCode,
                send_to=MESSAGE_ROUTE_TO_NONE,
            )
        return None

    async def _think(self) -> Action | None:
        if not CONFIG.src_workspace:
            CONFIG.src_workspace = CONFIG.git_repo.workdir / CONFIG.git_repo.workdir.name
        if not self.code_todos:
            await self._new_code_actions()
        elif not self.summarize_todos:
            await self._new_summarize_actions()
        else:
            return None
        return self._rc.todo  # For agent store

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
                task_doc = task_file_repo.get(i.filename)
            elif str(i.parent) == SYSTEM_DESIGN_FILE_REPO:
                design_doc = design_file_repo.get(i.filename)
        context = CodingContext(filename=filename, design_doc=design_doc, task_doc=task_doc, code_doc=old_code_doc)
        return context

    @staticmethod
    async def _new_coding_doc(filename, src_file_repo, task_file_repo, design_file_repo, dependency):
        context = await Engineer._new_coding_context(
            filename, src_file_repo, task_file_repo, design_file_repo, dependency
        )
        coding_doc = Document(root_path=str(src_file_repo.root_path), filename=filename, content=context.json())
        return coding_doc

    # =======
    #     async def _act(self) -> Message:
    #         """Determines the mode of action based on whether code review is used."""
    #         logger.info(f"{self._setting}: ready to WriteCode")
    #         if self.use_code_review:
    #             return await self._act_sp_with_cr()
    #         return await self._act_sp()
    # >>>>>>> feature/geekan_cli_etc

    async def _new_code_actions(self):
        # Prepare file repos
        src_file_repo = CONFIG.git_repo.new_file_repository(CONFIG.src_workspace)
        changed_src_files = src_file_repo.changed_files
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
        changed_src_files = src_file_repo.changed_files
        # Generate a SummarizeCode action for each pair of (system_design_doc, task_doc).
        summerizations = {}
        for filename in changed_src_files:
            depenencies = src_file_repo.get_dependency(filename=filename)
            ctx = CodeSummarizeContext.loads(filenames=depenencies)
            if ctx not in summerizations:
                summerizations[ctx] = set()
            srcs = summerizations.get(ctx)
            srcs.add(filename)
        for ctx, filenames in summerizations.items():
            ctx.codes_filenames = filenames
            self.summarize_todos.append(SummarizeCode(context=ctx, llm=self._llm))
        if self.summarize_todos:
            self._rc.todo = self.summarize_todos[0]
