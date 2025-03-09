#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : project_management.py
@Modified By: mashenquan, 2023/11/27.
        1. Divide the context into three components: legacy code, unit test code, and console log.
        2. Move the document storage operations related to WritePRD from the save operation of WriteDesign.
        3. According to the design in Section 2.2.3.5.4 of RFC 135, add incremental iteration functionality.
@Modified By: mashenquan, 2024/5/31. Implement Chapter 3 of RFC 236.
"""

import json
from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel, Field

from metagpt.actions.action import Action
from metagpt.actions.project_management_an import PM_NODE, REFINED_PM_NODE
from metagpt.const import PACKAGE_REQUIREMENTS_FILENAME
from metagpt.logs import logger
from metagpt.schema import AIMessage, Document, Documents, Message
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import (
    aread,
    awrite,
    rectify_pathname,
    save_json_to_markdown,
    to_markdown_code_block,
)
from metagpt.utils.project_repo import ProjectRepo
from metagpt.utils.report import DocsReporter

NEW_REQ_TEMPLATE = """
### Legacy Content
{old_task}

### New Requirements
{context}
"""


@register_tool(include_functions=["run"])
class WriteTasks(Action):
    name: str = "CreateTasks"
    i_context: Optional[str] = None
    repo: Optional[ProjectRepo] = Field(default=None, exclude=True)
    input_args: Optional[BaseModel] = Field(default=None, exclude=True)

    async def run(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        design_filename: str = "",
        output_pathname: str = "",
        **kwargs,
    ) -> Union[AIMessage, str]:
        """
        Write a project schedule given a project system design file.

        Args:
            user_requirement (str, optional): A string specifying the user's requirements. Defaults to an empty string.
            design_filename (str): The output file path of the document. Defaults to an empty string.
            output_pathname (str, optional): The output path name of file that the project schedule should be saved to.
            **kwargs: Additional keyword arguments.

        Returns:
            str: Path to the generated project schedule.

        Example:
            # Write a project schedule with a given system design.
            >>> design_filename = "/absolute/path/to/snake_game/docs/system_design.json"
            >>> output_pathname = "/absolute/path/to/snake_game/docs/project_schedule.json"
            >>> user_requirement = "Write project schedule for a snake game following these requirements:..."
            >>> action = WriteTasks()
            >>> result = await action.run(user_requirement=user_requirement, design_filename=design_filename, output_pathname=output_pathname)
            >>> print(result)
            The project schedule is at /absolute/path/to/snake_game/docs/project_schedule.json

            # Write a project schedule with a user requirement.
            >>> user_requirement = "Write project schedule for a snake game following these requirements: ..."
            >>> output_pathname = "/absolute/path/to/snake_game/docs/project_schedule.json"
            >>> action = WriteTasks()
            >>> result = await action.run(user_requirement=user_requirement, output_pathname=output_pathname)
            >>> print(result)
            The project schedule is at /absolute/path/to/snake_game/docs/project_schedule.json
        """
        if not with_messages:
            return await self._execute_api(
                user_requirement=user_requirement, design_filename=design_filename, output_pathname=output_pathname
            )

        self.input_args = with_messages[-1].instruct_content
        self.repo = ProjectRepo(self.input_args.project_path)
        changed_system_designs = self.input_args.changed_system_design_filenames
        changed_tasks = [str(self.repo.docs.task.workdir / i) for i in list(self.repo.docs.task.changed_files.keys())]
        change_files = Documents()
        # Rewrite the system designs that have undergone changes based on the git head diff under
        # `docs/system_designs/`.
        for filename in changed_system_designs:
            task_doc = await self._update_tasks(filename=filename)
            change_files.docs[str(self.repo.docs.task.workdir / task_doc.filename)] = task_doc

        # Rewrite the task files that have undergone changes based on the git head diff under `docs/tasks/`.
        for filename in changed_tasks:
            if filename in change_files.docs:
                continue
            task_doc = await self._update_tasks(filename=filename)
            change_files.docs[filename] = task_doc

        if not change_files.docs:
            logger.info("Nothing has changed.")
        # Wait until all files under `docs/tasks/` are processed before sending the publish_message, leaving room for
        # global optimization in subsequent steps.
        kvs = self.input_args.model_dump()
        kvs["changed_task_filenames"] = [
            str(self.repo.docs.task.workdir / i) for i in list(self.repo.docs.task.changed_files.keys())
        ]
        kvs["python_package_dependency_filename"] = str(self.repo.workdir / PACKAGE_REQUIREMENTS_FILENAME)
        return AIMessage(
            content="WBS is completed. "
            + "\n".join(
                [PACKAGE_REQUIREMENTS_FILENAME]
                + list(self.repo.docs.task.changed_files.keys())
                + list(self.repo.resources.api_spec_and_task.changed_files.keys())
            ),
            instruct_content=AIMessage.create_instruct_value(kvs=kvs, class_name="WriteTaskOutput"),
            cause_by=self,
        )

    async def _update_tasks(self, filename):
        root_relative_path = Path(filename).relative_to(self.repo.workdir)
        system_design_doc = await Document.load(filename=filename, project_path=self.repo.workdir)
        task_doc = await self.repo.docs.task.get(root_relative_path.name)
        async with DocsReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "task"}, "meta")
            if task_doc:
                task_doc = await self._merge(system_design_doc=system_design_doc, task_doc=task_doc)
                await self.repo.docs.task.save_doc(doc=task_doc, dependencies={system_design_doc.root_relative_path})
            else:
                rsp = await self._run_new_tasks(context=system_design_doc.content)
                task_doc = await self.repo.docs.task.save(
                    filename=system_design_doc.filename,
                    content=rsp.instruct_content.model_dump_json(),
                    dependencies={system_design_doc.root_relative_path},
                )
            await self._update_requirements(task_doc)
            md = await self.repo.resources.api_spec_and_task.save_pdf(doc=task_doc)
            await reporter.async_report(self.repo.workdir / md.root_relative_path, "path")
        return task_doc

    async def _run_new_tasks(self, context: str):
        node = await PM_NODE.fill(req=context, llm=self.llm, schema=self.prompt_schema)
        return node

    async def _merge(self, system_design_doc, task_doc) -> Document:
        context = NEW_REQ_TEMPLATE.format(context=system_design_doc.content, old_task=task_doc.content)
        node = await REFINED_PM_NODE.fill(req=context, llm=self.llm, schema=self.prompt_schema)
        task_doc.content = node.instruct_content.model_dump_json()
        return task_doc

    async def _update_requirements(self, doc):
        m = json.loads(doc.content)
        packages = set(m.get("Required packages", set()))
        requirement_doc = await self.repo.get(filename=PACKAGE_REQUIREMENTS_FILENAME)
        if not requirement_doc:
            requirement_doc = Document(filename=PACKAGE_REQUIREMENTS_FILENAME, root_path=".", content="")
        lines = requirement_doc.content.splitlines()
        for pkg in lines:
            if pkg == "":
                continue
            packages.add(pkg)
        await self.repo.save(filename=PACKAGE_REQUIREMENTS_FILENAME, content="\n".join(packages))

    async def _execute_api(
        self, user_requirement: str = "", design_filename: str = "", output_pathname: str = ""
    ) -> str:
        context = to_markdown_code_block(user_requirement)
        if design_filename:
            design_filename = rectify_pathname(path=design_filename, default_filename="system_design.md")
            content = await aread(filename=design_filename)
            context += to_markdown_code_block(content)

        async with DocsReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "task"}, "meta")
            node = await self._run_new_tasks(context)
            file_content = node.instruct_content.model_dump_json()

            if not output_pathname:
                output_pathname = Path(output_pathname) / "docs" / "project_schedule.json"
            elif not Path(output_pathname).is_absolute():
                output_pathname = self.config.workspace.path / output_pathname
            output_pathname = rectify_pathname(path=output_pathname, default_filename="project_schedule.json")
            await awrite(filename=output_pathname, data=file_content)
            md_output_filename = output_pathname.with_suffix(".md")
            await save_json_to_markdown(content=file_content, output_filename=md_output_filename)
            await reporter.async_report(md_output_filename, "path")
        return f'Project Schedule filename: "{str(output_pathname)}"'
