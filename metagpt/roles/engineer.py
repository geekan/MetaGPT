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

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Optional, Set

from metagpt.actions import Action, WriteCode, WriteCodeReview, WriteTasks
from metagpt.actions.fix_bug import FixBug
from metagpt.actions.project_management_an import REFINED_TASK_LIST, TASK_LIST
from metagpt.actions.summarize_code import SummarizeCode
from metagpt.actions.write_code_plan_and_change_an import WriteCodePlanAndChange
from metagpt.const import (
    BUGFIX_FILENAME,
    CODE_PLAN_AND_CHANGE_FILE_REPO,
    REQUIREMENT_FILENAME,
    SYSTEM_DESIGN_FILE_REPO,
    TASK_FILE_REPO,
)
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import (
    CodePlanAndChangeContext,
    CodeSummarizeContext,
    CodingContext,
    Document,
    Documents,
    Message,
)
from metagpt.utils.common import any_to_name, any_to_str, any_to_str_set

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

    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = "write elegant, readable, extensible, efficient code"
    constraints: str = (
        "the code should conform to standards like google-style and be modular and maintainable. "
        "Use same language as user requirement"
    )
    n_borg: int = 1
    use_code_review: bool = False
    code_todos: list = []
    summarize_todos: list = []
    next_todo_action: str = ""
    n_summarize: int = 0

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.set_actions([WriteCode])
        self._watch([WriteTasks, SummarizeCode, WriteCode, WriteCodeReview, FixBug, WriteCodePlanAndChange])
        self.code_todos = []
        self.summarize_todos = []
        self.next_todo_action = any_to_name(WriteCode)

    @staticmethod
    def _parse_tasks(task_msg: Document) -> list[str]:
        m = json.loads(task_msg.content)
        return m.get(TASK_LIST.key) or m.get(REFINED_TASK_LIST.key)

    async def _act_sp_with_cr(self, review=False) -> Set[str]:
        changed_files = set()
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
                action = WriteCodeReview(i_context=coding_context, context=self.context, llm=self.llm)
                self._init_action(action)
                coding_context = await action.run()

            dependencies = {coding_context.design_doc.root_relative_path, coding_context.task_doc.root_relative_path}
            if self.config.inc:
                dependencies.add(coding_context.code_plan_and_change_doc.root_relative_path)
            await self.project_repo.srcs.save(
                filename=coding_context.filename,
                dependencies=list(dependencies),
                content=coding_context.code_doc.content,
            )
            msg = Message(
                content=coding_context.model_dump_json(),
                instruct_content=coding_context,
                role=self.profile,
                cause_by=WriteCode,
            )
            self.rc.memory.add(msg)

            changed_files.add(coding_context.code_doc.filename)
        if not changed_files:
            logger.info("Nothing has changed.")
        return changed_files

    async def _act(self) -> Message | None:
        """Determines the mode of action based on whether code review is used."""
        if self.rc.todo is None:
            return None
        if isinstance(self.rc.todo, WriteCodePlanAndChange):
            self.next_todo_action = any_to_name(WriteCode)
            return await self._act_code_plan_and_change()
        if isinstance(self.rc.todo, WriteCode):
            self.next_todo_action = any_to_name(SummarizeCode)
            return await self._act_write_code()
        if isinstance(self.rc.todo, SummarizeCode):
            self.next_todo_action = any_to_name(WriteCode)
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
        )

    async def _act_summarize(self):
        tasks = []
        for todo in self.summarize_todos:
            summary = await todo.run()
            summary_filename = Path(todo.i_context.design_filename).with_suffix(".md").name
            dependencies = {todo.i_context.design_filename, todo.i_context.task_filename}
            for filename in todo.i_context.codes_filenames:
                rpath = self.project_repo.src_relative_path / filename
                dependencies.add(str(rpath))
            await self.project_repo.resources.code_summary.save(
                filename=summary_filename, content=summary, dependencies=dependencies
            )
            is_pass, reason = await self._is_pass(summary)
            if not is_pass:
                todo.i_context.reason = reason
                tasks.append(todo.i_context.model_dump())

                await self.project_repo.docs.code_summary.save(
                    filename=Path(todo.i_context.design_filename).name,
                    content=todo.i_context.model_dump_json(),
                    dependencies=dependencies,
                )
            else:
                await self.project_repo.docs.code_summary.delete(filename=Path(todo.i_context.design_filename).name)

        logger.info(f"--max-auto-summarize-code={self.config.max_auto_summarize_code}")
        if not tasks or self.config.max_auto_summarize_code == 0:
            return Message(
                content="",
                role=self.profile,
                cause_by=SummarizeCode,
                sent_from=self,
                send_to="Edward",  # The name of QaEngineer
            )
        # The maximum number of times the 'SummarizeCode' action is automatically invoked, with -1 indicating unlimited.
        # This parameter is used for debugging the workflow.
        self.n_summarize += 1 if self.config.max_auto_summarize_code > self.n_summarize else 0
        return Message(
            content=json.dumps(tasks), role=self.profile, cause_by=SummarizeCode, send_to=self, sent_from=self
        )

    async def _act_code_plan_and_change(self):
        """Write code plan and change that guides subsequent WriteCode and WriteCodeReview"""
        node = await self.rc.todo.run()
        code_plan_and_change = node.instruct_content.model_dump_json()
        dependencies = {
            REQUIREMENT_FILENAME,
            str(self.project_repo.docs.prd.root_path / self.rc.todo.i_context.prd_filename),
            str(self.project_repo.docs.system_design.root_path / self.rc.todo.i_context.design_filename),
            str(self.project_repo.docs.task.root_path / self.rc.todo.i_context.task_filename),
        }
        code_plan_and_change_filepath = Path(self.rc.todo.i_context.design_filename)
        await self.project_repo.docs.code_plan_and_change.save(
            filename=code_plan_and_change_filepath.name, content=code_plan_and_change, dependencies=dependencies
        )
        await self.project_repo.resources.code_plan_and_change.save(
            filename=code_plan_and_change_filepath.with_suffix(".md").name,
            content=node.content,
            dependencies=dependencies,
        )

        return Message(
            content=code_plan_and_change,
            role=self.profile,
            cause_by=WriteCodePlanAndChange,
            send_to=self,
            sent_from=self,
        )

    async def _is_pass(self, summary) -> (str, str):
        rsp = await self.llm.aask(msg=IS_PASS_PROMPT.format(context=summary), stream=False)
        logger.info(rsp)
        if "YES" in rsp:
            return True, rsp
        return False, rsp

    async def _think(self) -> Action | None:
        if not self.src_workspace:
            self.src_workspace = self.git_repo.workdir / self.git_repo.workdir.name
        write_plan_and_change_filters = any_to_str_set([WriteTasks, FixBug])
        write_code_filters = any_to_str_set([WriteTasks, WriteCodePlanAndChange, SummarizeCode])
        summarize_code_filters = any_to_str_set([WriteCode, WriteCodeReview])
        if not self.rc.news:
            return None
        msg = self.rc.news[0]
        if self.config.inc and msg.cause_by in write_plan_and_change_filters:
            logger.debug(f"TODO WriteCodePlanAndChange:{msg.model_dump_json()}")
            await self._new_code_plan_and_change_action(cause_by=msg.cause_by)
            return self.rc.todo
        if msg.cause_by in write_code_filters:
            logger.debug(f"TODO WriteCode:{msg.model_dump_json()}")
            await self._new_code_actions()
            return self.rc.todo
        if msg.cause_by in summarize_code_filters and msg.sent_from == any_to_str(self):
            logger.debug(f"TODO SummarizeCode:{msg.model_dump_json()}")
            await self._new_summarize_actions()
            return self.rc.todo
        return None

    async def _new_coding_context(self, filename, dependency) -> CodingContext:
        old_code_doc = await self.project_repo.srcs.get(filename)
        if not old_code_doc:
            old_code_doc = Document(root_path=str(self.project_repo.src_relative_path), filename=filename, content="")
        dependencies = {Path(i) for i in await dependency.get(old_code_doc.root_relative_path)}
        task_doc = None
        design_doc = None
        code_plan_and_change_doc = await self._get_any_code_plan_and_change() if await self._is_fixbug() else None
        for i in dependencies:
            if str(i.parent.as_posix()) == TASK_FILE_REPO:
                task_doc = await self.project_repo.docs.task.get(i.name)
            elif str(i.parent.as_posix()) == SYSTEM_DESIGN_FILE_REPO:
                design_doc = await self.project_repo.docs.system_design.get(i.name)
            elif str(i.parent.as_posix()) == CODE_PLAN_AND_CHANGE_FILE_REPO:
                code_plan_and_change_doc = await self.project_repo.docs.code_plan_and_change.get(i.name)
        if not task_doc or not design_doc:
            logger.error(f'Detected source code "{filename}" from an unknown origin.')
            raise ValueError(f'Detected source code "{filename}" from an unknown origin.')
        context = CodingContext(
            filename=filename,
            design_doc=design_doc,
            task_doc=task_doc,
            code_doc=old_code_doc,
            code_plan_and_change_doc=code_plan_and_change_doc,
        )
        return context

    async def _new_coding_doc(self, filename, dependency):
        context = await self._new_coding_context(filename, dependency)
        coding_doc = Document(
            root_path=str(self.project_repo.src_relative_path), filename=filename, content=context.model_dump_json()
        )
        return coding_doc

    async def _new_code_actions(self):
        bug_fix = await self._is_fixbug()
        # Prepare file repos
        changed_src_files = self.project_repo.srcs.all_files if bug_fix else self.project_repo.srcs.changed_files
        changed_task_files = self.project_repo.docs.task.changed_files
        changed_files = Documents()
        # Recode caused by upstream changes.
        for filename in changed_task_files:
            design_doc = await self.project_repo.docs.system_design.get(filename)
            task_doc = await self.project_repo.docs.task.get(filename)
            code_plan_and_change_doc = await self.project_repo.docs.code_plan_and_change.get(filename)
            task_list = self._parse_tasks(task_doc)
            for task_filename in task_list:
                old_code_doc = await self.project_repo.srcs.get(task_filename)
                if not old_code_doc:
                    old_code_doc = Document(
                        root_path=str(self.project_repo.src_relative_path), filename=task_filename, content=""
                    )
                if not code_plan_and_change_doc:
                    context = CodingContext(
                        filename=task_filename, design_doc=design_doc, task_doc=task_doc, code_doc=old_code_doc
                    )
                else:
                    context = CodingContext(
                        filename=task_filename,
                        design_doc=design_doc,
                        task_doc=task_doc,
                        code_doc=old_code_doc,
                        code_plan_and_change_doc=code_plan_and_change_doc,
                    )
                coding_doc = Document(
                    root_path=str(self.project_repo.src_relative_path),
                    filename=task_filename,
                    content=context.model_dump_json(),
                )
                if task_filename in changed_files.docs:
                    logger.warning(
                        f"Log to expose potential conflicts: {coding_doc.model_dump_json()} & "
                        f"{changed_files.docs[task_filename].model_dump_json()}"
                    )
                changed_files.docs[task_filename] = coding_doc
        self.code_todos = [
            WriteCode(i_context=i, context=self.context, llm=self.llm) for i in changed_files.docs.values()
        ]
        # Code directly modified by the user.
        dependency = await self.git_repo.get_dependency()
        for filename in changed_src_files:
            if filename in changed_files.docs:
                continue
            coding_doc = await self._new_coding_doc(filename=filename, dependency=dependency)
            changed_files.docs[filename] = coding_doc
            self.code_todos.append(WriteCode(i_context=coding_doc, context=self.context, llm=self.llm))

        if self.code_todos:
            self.set_todo(self.code_todos[0])

    async def _new_summarize_actions(self):
        src_files = self.project_repo.srcs.all_files
        # Generate a SummarizeCode action for each pair of (system_design_doc, task_doc).
        summarizations = defaultdict(list)
        for filename in src_files:
            dependencies = await self.project_repo.srcs.get_dependency(filename=filename)
            ctx = CodeSummarizeContext.loads(filenames=list(dependencies))
            summarizations[ctx].append(filename)
        for ctx, filenames in summarizations.items():
            ctx.codes_filenames = filenames
            new_summarize = SummarizeCode(i_context=ctx, context=self.context, llm=self.llm)
            for i, act in enumerate(self.summarize_todos):
                if act.i_context.task_filename == new_summarize.i_context.task_filename:
                    self.summarize_todos[i] = new_summarize
                    new_summarize = None
                    break
            if new_summarize:
                self.summarize_todos.append(new_summarize)
        if self.summarize_todos:
            self.set_todo(self.summarize_todos[0])
            self.summarize_todos.pop(0)

    async def _new_code_plan_and_change_action(self, cause_by: str):
        """Create a WriteCodePlanAndChange action for subsequent to-do actions."""
        files = self.project_repo.all_files
        options = {}
        if cause_by != any_to_str(FixBug):
            requirement_doc = await self.project_repo.docs.get(REQUIREMENT_FILENAME)
            options["requirement"] = requirement_doc.content
        else:
            fixbug_doc = await self.project_repo.docs.get(BUGFIX_FILENAME)
            options["issue"] = fixbug_doc.content
        code_plan_and_change_ctx = CodePlanAndChangeContext.loads(files, **options)
        self.rc.todo = WriteCodePlanAndChange(i_context=code_plan_and_change_ctx, context=self.context, llm=self.llm)

    @property
    def action_description(self) -> str:
        """AgentStore uses this attribute to display to the user what actions the current role should take."""
        return self.next_todo_action

    async def _is_fixbug(self) -> bool:
        fixbug_doc = await self.project_repo.docs.get(BUGFIX_FILENAME)
        return bool(fixbug_doc and fixbug_doc.content)

    async def _get_any_code_plan_and_change(self) -> Optional[Document]:
        changed_files = self.project_repo.docs.code_plan_and_change.changed_files
        for filename in changed_files.keys():
            doc = await self.project_repo.docs.code_plan_and_change.get(filename)
            if doc and doc.content:
                return doc
        return None
