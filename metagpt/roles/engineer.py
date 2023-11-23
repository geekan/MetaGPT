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
"""
from __future__ import annotations

import json
from pathlib import Path

from metagpt.actions import Action, WriteCode, WriteCodeReview, WriteTasks
from metagpt.config import CONFIG
from metagpt.const import SYSTEM_DESIGN_FILE_REPO, TASK_FILE_REPO
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import CodingContext, Document, Documents, Message
from metagpt.utils.special_tokens import FILENAME_CODE_SEP, MSG_SEP


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
    ) -> None:
        """Initializes the Engineer role with given attributes."""
        super().__init__(name, profile, goal, constraints)
        self.use_code_review = use_code_review
        self._watch([WriteTasks])
        self.todos = []
        self.n_borg = n_borg

    @staticmethod
    def _parse_tasks(task_msg: Document) -> list[str]:
        m = json.loads(task_msg.content)
        return m.get("Task list")

    async def _act_sp_precision(self, review=False) -> Message:
        code_msg_all = []  # gather all code info, will pass to qa_engineer for tests later
        src_file_repo = CONFIG.git_repo.new_file_repository(CONFIG.src_workspace)
        for todo in self.todos:
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
                try:
                    coding_context = await WriteCodeReview(context=coding_context, llm=self._llm).run()
                except Exception as e:
                    logger.error("code review failed!", e)
                    pass
            await src_file_repo.save(
                coding_context.filename,
                dependencies={coding_context.design_doc.root_relative_path, coding_context.task_doc.root_relative_path},
                content=coding_context.code_doc.content,
            )
            msg = Message(
                content=coding_context.json(), instruct_content=coding_context, role=self.profile, cause_by=WriteCode
            )
            self._rc.memory.add(msg)
            self.publish_message(msg)

            code_msg = coding_context.filename + FILENAME_CODE_SEP + str(coding_context.code_doc.root_relative_path)
            code_msg_all.append(code_msg)

        logger.info(f"Done {CONFIG.src_workspace} generating.")
        msg = Message(
            content=MSG_SEP.join(code_msg_all),
            role=self.profile,
            cause_by=self._rc.todo,
            send_to="Edward",
        )
        return msg

    async def _act(self) -> Message:
        """Determines the mode of action based on whether code review is used."""
        return await self._act_sp_precision(review=self.use_code_review)

    async def _think(self) -> Action | None:
        if not CONFIG.src_workspace:
            CONFIG.src_workspace = CONFIG.git_repo.workdir / CONFIG.git_repo.workdir.name
        # Prepare file repos
        src_file_repo = CONFIG.git_repo.new_file_repository(CONFIG.src_workspace)
        changed_src_files = src_file_repo.changed_files
        task_file_repo = CONFIG.git_repo.new_file_repository(TASK_FILE_REPO)
        changed_task_files = task_file_repo.changed_files
        design_file_repo = CONFIG.git_repo.new_file_repository(SYSTEM_DESIGN_FILE_REPO)

        changed_files = Documents()
        # 由上游变化导致的recode
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
                    logger.error(
                        f"Log to expose potential file name conflicts: {coding_doc.json()} & "
                        f"{changed_files.docs[task_filename].json()}"
                    )
                changed_files.docs[task_filename] = coding_doc
        self.todos = [WriteCode(context=i, llm=self._llm) for i in changed_files.docs.values()]
        # 用户直接修改的code
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
            self.todos.append(WriteCode(context=coding_doc, llm=self._llm))
        # 仅单测
        if CONFIG.REQA_FILENAME and CONFIG.REQA_FILENAME not in changed_files.docs:
            context = await self._new_coding_context(
                filename=CONFIG.REQA_FILENAME,
                src_file_repo=src_file_repo,
                task_file_repo=task_file_repo,
                design_file_repo=design_file_repo,
                dependency=dependency,
            )
            self.publish_message(Message(content=context.json(), instruct_content=context, cause_by=WriteCode))

        if self.todos:
            self._rc.todo = self.todos[0]
        return self._rc.todo  # For agent store

    @staticmethod
    async def _new_coding_context(
        filename, src_file_repo, task_file_repo, design_file_repo, dependency
    ) -> CodingContext:
        old_code_doc = await src_file_repo.get(filename)
        if not old_code_doc:
            old_code_doc = Document(root_path=str(src_file_repo.root_path), filename=filename, content="")
        dependencies = {Path(i) for i in dependency.get(old_code_doc.root_relative_path)}
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
