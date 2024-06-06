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
from typing import List, Optional, Set

from pydantic import BaseModel, Field

from metagpt.actions import WriteCode, WriteCodeReview, WriteTasks
from metagpt.actions.fix_bug import FixBug
from metagpt.actions.prepare_documents import PrepareDocuments
from metagpt.actions.project_management_an import REFINED_TASK_LIST, TASK_LIST
from metagpt.actions.summarize_code import SummarizeCode
from metagpt.actions.write_code_plan_and_change_an import WriteCodePlanAndChange
from metagpt.const import (
    CODE_PLAN_AND_CHANGE_FILE_REPO,
    MESSAGE_ROUTE_TO_SELF,
    REQUIREMENT_FILENAME,
    SYSTEM_DESIGN_FILE_REPO,
    TASK_FILE_REPO,
)
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import (
    AIMessage,
    CodePlanAndChangeContext,
    CodeSummarizeContext,
    CodingContext,
    Document,
    Documents,
    Message,
)
from metagpt.utils.common import (
    any_to_name,
    any_to_str,
    any_to_str_set,
    get_project_srcs_path,
    init_python_folder,
)
from metagpt.utils.git_repository import ChangeType
from metagpt.utils.project_repo import ProjectRepo

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
    input_args: Optional[BaseModel] = Field(default=None, exclude=True)
    repo: Optional[ProjectRepo] = Field(default=None, exclude=True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.enable_memory = False
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
                action = WriteCodeReview(
                    i_context=coding_context,
                    repo=self.repo,
                    input_args=self.input_args,
                    context=self.context,
                    llm=self.llm,
                )
                self._init_action(action)
                coding_context = await action.run()

            dependencies = {coding_context.design_doc.root_relative_path, coding_context.task_doc.root_relative_path}
            if self.config.inc:
                dependencies.add(coding_context.code_plan_and_change_doc.root_relative_path)
            await self.repo.srcs.save(
                filename=coding_context.filename,
                dependencies=list(dependencies),
                content=coding_context.code_doc.content,
            )
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
        return await self.rc.todo.run(self.rc.history)

    async def _act_write_code(self):
        await self._act_sp_with_cr(review=self.use_code_review)
        return AIMessage(
            content="", cause_by=WriteCodeReview if self.use_code_review else WriteCode, send_to=MESSAGE_ROUTE_TO_SELF
        )

    async def _act_summarize(self):
        tasks = []
        for todo in self.summarize_todos:
            if self.n_summarize >= self.config.max_auto_summarize_code:
                break
            summary = await todo.run()
            summary_filename = Path(todo.i_context.design_filename).with_suffix(".md").name
            dependencies = {todo.i_context.design_filename, todo.i_context.task_filename}
            for filename in todo.i_context.codes_filenames:
                rpath = self.repo.src_relative_path / filename
                dependencies.add(str(rpath))
            await self.repo.resources.code_summary.save(
                filename=summary_filename, content=summary, dependencies=dependencies
            )
            is_pass, reason = await self._is_pass(summary)
            if not is_pass:
                todo.i_context.reason = reason
                tasks.append(todo.i_context.model_dump())

                await self.repo.docs.code_summary.save(
                    filename=Path(todo.i_context.design_filename).name,
                    content=todo.i_context.model_dump_json(),
                    dependencies=dependencies,
                )
            else:
                await self.repo.docs.code_summary.delete(filename=Path(todo.i_context.design_filename).name)
        self.summarize_todos = []
        logger.info(f"--max-auto-summarize-code={self.config.max_auto_summarize_code}")
        if not tasks or self.config.max_auto_summarize_code == 0:
            self.n_summarize = 0
            kvs = self.input_args.model_dump()
            kvs["changed_src_filenames"] = [
                str(self.repo.srcs.workdir / i) for i in list(self.repo.srcs.changed_files.keys())
            ]
            if self.repo.docs.code_plan_and_change.changed_files:
                kvs["changed_code_plan_and_change_filenames"] = [
                    str(self.repo.docs.code_plan_and_change.workdir / i)
                    for i in list(self.repo.docs.code_plan_and_change.changed_files.keys())
                ]
            if self.repo.docs.code_summary.changed_files:
                kvs["changed_code_summary_filenames"] = [
                    str(self.repo.docs.code_summary.workdir / i)
                    for i in list(self.repo.docs.code_summary.changed_files.keys())
                ]
            return AIMessage(
                content=f"Coding is complete. The source code is at {self.repo.workdir.name}/{self.repo.srcs.root_path}, containing: "
                + "\n".join(
                    list(self.repo.resources.code_summary.changed_files.keys())
                    + list(self.repo.srcs.changed_files.keys())
                    + list(self.repo.resources.code_plan_and_change.changed_files.keys())
                ),
                instruct_content=AIMessage.create_instruct_value(kvs=kvs, class_name="SummarizeCodeOutput"),
                cause_by=SummarizeCode,
                send_to="Edward",  # The name of QaEngineer
            )
        # The maximum number of times the 'SummarizeCode' action is automatically invoked, with -1 indicating unlimited.
        # This parameter is used for debugging the workflow.
        self.n_summarize += 1 if self.config.max_auto_summarize_code > self.n_summarize else 0
        return AIMessage(content="", cause_by=SummarizeCode, send_to=MESSAGE_ROUTE_TO_SELF)

    async def _act_code_plan_and_change(self):
        """Write code plan and change that guides subsequent WriteCode and WriteCodeReview"""
        node = await self.rc.todo.run()
        code_plan_and_change = node.instruct_content.model_dump_json()
        dependencies = {
            REQUIREMENT_FILENAME,
            str(Path(self.rc.todo.i_context.prd_filename).relative_to(self.repo.workdir)),
            str(Path(self.rc.todo.i_context.design_filename).relative_to(self.repo.workdir)),
            str(Path(self.rc.todo.i_context.task_filename).relative_to(self.repo.workdir)),
        }
        code_plan_and_change_filepath = Path(self.rc.todo.i_context.design_filename)
        await self.repo.docs.code_plan_and_change.save(
            filename=code_plan_and_change_filepath.name, content=code_plan_and_change, dependencies=dependencies
        )
        await self.repo.resources.code_plan_and_change.save(
            filename=code_plan_and_change_filepath.with_suffix(".md").name,
            content=node.content,
            dependencies=dependencies,
        )

        return AIMessage(content="", cause_by=WriteCodePlanAndChange, send_to=MESSAGE_ROUTE_TO_SELF)

    async def _is_pass(self, summary) -> (str, str):
        rsp = await self.llm.aask(msg=IS_PASS_PROMPT.format(context=summary), stream=False)
        logger.info(rsp)
        if "YES" in rsp:
            return True, rsp
        return False, rsp

    async def _think(self) -> bool:
        if not self.rc.news:
            return False
        msg = self.rc.news[0]
        input_args = msg.instruct_content
        if msg.cause_by in {any_to_str(WriteTasks), any_to_str(FixBug)}:
            self.input_args = input_args
            self.repo = ProjectRepo(input_args.project_path)
            if self.repo.src_relative_path is None:
                path = get_project_srcs_path(self.repo.workdir)
                self.repo.with_src_path(path)
        write_plan_and_change_filters = any_to_str_set([PrepareDocuments, WriteTasks, FixBug])
        write_code_filters = any_to_str_set([WriteTasks, WriteCodePlanAndChange, SummarizeCode])
        summarize_code_filters = any_to_str_set([WriteCode, WriteCodeReview])
        if self.config.inc and msg.cause_by in write_plan_and_change_filters:
            logger.debug(f"TODO WriteCodePlanAndChange:{msg.model_dump_json()}")
            await self._new_code_plan_and_change_action(cause_by=msg.cause_by)
            return bool(self.rc.todo)
        if msg.cause_by in write_code_filters:
            logger.debug(f"TODO WriteCode:{msg.model_dump_json()}")
            await self._new_code_actions()
            return bool(self.rc.todo)
        if msg.cause_by in summarize_code_filters and msg.sent_from == any_to_str(self):
            logger.debug(f"TODO SummarizeCode:{msg.model_dump_json()}")
            await self._new_summarize_actions()
            return bool(self.rc.todo)
        return False

    async def _new_coding_context(self, filename, dependency) -> Optional[CodingContext]:
        old_code_doc = await self.repo.srcs.get(filename)
        if not old_code_doc:
            old_code_doc = Document(root_path=str(self.repo.src_relative_path), filename=filename, content="")
        dependencies = {Path(i) for i in await dependency.get(old_code_doc.root_relative_path)}
        task_doc = None
        design_doc = None
        code_plan_and_change_doc = await self._get_any_code_plan_and_change() if await self._is_fixbug() else None
        for i in dependencies:
            if str(i.parent) == TASK_FILE_REPO:
                task_doc = await self.repo.docs.task.get(i.name)
            elif str(i.parent) == SYSTEM_DESIGN_FILE_REPO:
                design_doc = await self.repo.docs.system_design.get(i.name)
            elif str(i.parent) == CODE_PLAN_AND_CHANGE_FILE_REPO:
                code_plan_and_change_doc = await self.repo.docs.code_plan_and_change.get(i.name)
        if not task_doc or not design_doc:
            if filename == "__init__.py":  # `__init__.py` created by `init_python_folder`
                return None
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

    async def _new_coding_doc(self, filename, dependency) -> Optional[Document]:
        context = await self._new_coding_context(filename, dependency)
        if not context:
            return None  # `__init__.py` created by `init_python_folder`
        coding_doc = Document(
            root_path=str(self.repo.src_relative_path), filename=filename, content=context.model_dump_json()
        )
        return coding_doc

    async def _new_code_actions(self):
        bug_fix = await self._is_fixbug()
        # Prepare file repos
        changed_src_files = self.repo.srcs.changed_files
        if self.context.kwargs.src_filename:
            changed_src_files = {self.context.kwargs.src_filename: ChangeType.UNTRACTED}
        if bug_fix:
            changed_src_files = self.repo.srcs.all_files
        changed_files = Documents()
        # Recode caused by upstream changes.
        if hasattr(self.input_args, "changed_task_filenames"):
            changed_task_filenames = self.input_args.changed_task_filenames
        else:
            changed_task_filenames = [
                str(self.repo.docs.task.workdir / i) for i in list(self.repo.docs.task.changed_files.keys())
            ]
        for filename in changed_task_filenames:
            task_filename = Path(filename)
            design_filename = None
            if hasattr(self.input_args, "changed_system_design_filenames"):
                changed_system_design_filenames = self.input_args.changed_system_design_filenames
            else:
                changed_system_design_filenames = [
                    str(self.repo.docs.system_design.workdir / i)
                    for i in list(self.repo.docs.system_design.changed_files.keys())
                ]
            for i in changed_system_design_filenames:
                if task_filename.name == Path(i).name:
                    design_filename = Path(i)
                    break
            code_plan_and_change_filename = None
            if hasattr(self.input_args, "changed_code_plan_and_change_filenames"):
                changed_code_plan_and_change_filenames = self.input_args.changed_code_plan_and_change_filenames
            else:
                changed_code_plan_and_change_filenames = [
                    str(self.repo.docs.code_plan_and_change.workdir / i)
                    for i in list(self.repo.docs.code_plan_and_change.changed_files.keys())
                ]
            for i in changed_code_plan_and_change_filenames:
                if task_filename.name == Path(i).name:
                    code_plan_and_change_filename = Path(i)
                    break
            design_doc = await Document.load(filename=design_filename, project_path=self.repo.workdir)
            task_doc = await Document.load(filename=task_filename, project_path=self.repo.workdir)
            code_plan_and_change_doc = await Document.load(
                filename=code_plan_and_change_filename, project_path=self.repo.workdir
            )
            task_list = self._parse_tasks(task_doc)
            await self._init_python_folder(task_list)
            for task_filename in task_list:
                if self.context.kwargs.src_filename and task_filename != self.context.kwargs.src_filename:
                    continue
                old_code_doc = await self.repo.srcs.get(task_filename)
                if not old_code_doc:
                    old_code_doc = Document(
                        root_path=str(self.repo.src_relative_path), filename=task_filename, content=""
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
                    root_path=str(self.repo.src_relative_path),
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
            WriteCode(i_context=i, repo=self.repo, input_args=self.input_args, context=self.context, llm=self.llm)
            for i in changed_files.docs.values()
        ]
        # Code directly modified by the user.
        dependency = await self.repo.git_repo.get_dependency()
        for filename in changed_src_files:
            if filename in changed_files.docs:
                continue
            coding_doc = await self._new_coding_doc(filename=filename, dependency=dependency)
            if not coding_doc:
                continue  # `__init__.py` created by `init_python_folder`
            changed_files.docs[filename] = coding_doc
            self.code_todos.append(
                WriteCode(
                    i_context=coding_doc, repo=self.repo, input_args=self.input_args, context=self.context, llm=self.llm
                )
            )

        if self.code_todos:
            self.set_todo(self.code_todos[0])

    async def _new_summarize_actions(self):
        src_files = self.repo.srcs.all_files
        # Generate a SummarizeCode action for each pair of (system_design_doc, task_doc).
        summarizations = defaultdict(list)
        for filename in src_files:
            dependencies = await self.repo.srcs.get_dependency(filename=filename)
            ctx = CodeSummarizeContext.loads(filenames=list(dependencies))
            summarizations[ctx].append(filename)
        for ctx, filenames in summarizations.items():
            if not ctx.design_filename or not ctx.task_filename:
                continue  # cause by `__init__.py` which is created by `init_python_folder`
            ctx.codes_filenames = filenames
            new_summarize = SummarizeCode(
                i_context=ctx, repo=self.repo, input_args=self.input_args, context=self.context, llm=self.llm
            )
            for i, act in enumerate(self.summarize_todos):
                if act.i_context.task_filename == new_summarize.i_context.task_filename:
                    self.summarize_todos[i] = new_summarize
                    new_summarize = None
                    break
            if new_summarize:
                self.summarize_todos.append(new_summarize)
        if self.summarize_todos:
            self.set_todo(self.summarize_todos[0])

    async def _new_code_plan_and_change_action(self, cause_by: str):
        """Create a WriteCodePlanAndChange action for subsequent to-do actions."""
        options = {}
        if cause_by != any_to_str(FixBug):
            requirement_doc = await Document.load(filename=self.input_args.requirements_filename)
            options["requirement"] = requirement_doc.content
        else:
            fixbug_doc = await Document.load(filename=self.input_args.issue_filename)
            options["issue"] = fixbug_doc.content
        # The code here is flawed: if there are multiple unrelated requirements, this piece of logic will break
        if hasattr(self.input_args, "changed_prd_filenames"):
            code_plan_and_change_ctx = CodePlanAndChangeContext(
                requirement=options.get("requirement", ""),
                issue=options.get("issue", ""),
                prd_filename=self.input_args.changed_prd_filenames[0],
                design_filename=self.input_args.changed_system_design_filenames[0],
                task_filename=self.input_args.changed_task_filenames[0],
            )
        else:
            code_plan_and_change_ctx = CodePlanAndChangeContext(
                requirement=options.get("requirement", ""),
                issue=options.get("issue", ""),
                prd_filename=str(self.repo.docs.prd.workdir / self.repo.docs.prd.all_files[0]),
                design_filename=str(self.repo.docs.system_design.workdir / self.repo.docs.system_design.all_files[0]),
                task_filename=str(self.repo.docs.task.workdir / self.repo.docs.task.all_files[0]),
            )
        self.rc.todo = WriteCodePlanAndChange(
            i_context=code_plan_and_change_ctx,
            repo=self.repo,
            input_args=self.input_args,
            context=self.context,
            llm=self.llm,
        )

    @property
    def action_description(self) -> str:
        """AgentStore uses this attribute to display to the user what actions the current role should take."""
        return self.next_todo_action

    async def _init_python_folder(self, task_list: List[str]):
        for i in task_list:
            filename = Path(i)
            if filename.suffix != ".py":
                continue
            workdir = self.repo.srcs.workdir / filename.parent
            if not workdir.exists():
                workdir = self.repo.workdir / filename.parent
            await init_python_folder(workdir)

    async def _is_fixbug(self) -> bool:
        return bool(self.input_args and hasattr(self.input_args, "issue_filename"))

    async def _get_any_code_plan_and_change(self) -> Optional[Document]:
        changed_files = self.repo.docs.code_plan_and_change.changed_files
        for filename in changed_files.keys():
            doc = await self.repo.docs.code_plan_and_change.get(filename)
            if doc and doc.content:
                return doc
        return None
