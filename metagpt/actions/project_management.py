#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/11 19:12
# @Author  : alexanderwu
# @File    : project_management.py
# @Modified By: mashenquan, 2023/11/27.
#         1. Divide the context into three components: legacy code, unit test code, and console log.
#         2. Move the document storage operations related to WritePRD from the save operation of WriteDesign.
#         3. According to the design in Section 2.2.3.5.4 of RFC 135, add incremental iteration functionality.

import json
from typing import Optional

from metagpt.actions.action import Action
from metagpt.actions.action_output import ActionOutput
from metagpt.actions.project_management_an import PM_NODE, REFINED_PM_NODE
from metagpt.const import PACKAGE_REQUIREMENTS_FILENAME
from metagpt.logs import logger
from metagpt.schema import Document, Documents

NEW_REQ_TEMPLATE = """
### Legacy Content
{old_task}

### New Requirements
{context}
"""


class WriteTasks(Action):
    """Handles the creation and updating of tasks based on system design changes.

    This class extends the Action class to implement the functionality for creating and updating tasks
    based on changes in system designs. It checks for changed files in the system design and task directories,
    merges new requirements with existing tasks if necessary, and updates the tasks accordingly.

    Attributes:
        name: A string indicating the name of the action.
        i_context: An optional string that provides additional context for the action.
    """

    name: str = "CreateTasks"
    i_context: Optional[str] = None

    async def run(self, with_messages):
        """Executes the action to create or update tasks.

        This method checks for changed system design and task files, updates tasks based on the changes,
        and saves the updated tasks. If there are no changes, it logs a message indicating so.

        Args:
            with_messages: A flag indicating whether to include messages in the output.

        Returns:
            An ActionOutput object containing the updated tasks and any instructions.
        """
        changed_system_designs = self.repo.docs.system_design.changed_files
        changed_tasks = self.repo.docs.task.changed_files
        change_files = Documents()
        # Rewrite the system designs that have undergone changes based on the git head diff under
        # `docs/system_designs/`.
        for filename in changed_system_designs:
            task_doc = await self._update_tasks(filename=filename)
            change_files.docs[filename] = task_doc

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
        return ActionOutput(content=change_files.model_dump_json(), instruct_content=change_files)

    async def _update_tasks(self, filename):
        """Updates tasks based on a given filename.

        This method retrieves the system design and task documents based on the filename, merges new requirements
        with existing tasks if necessary, and saves the updated task document.

        Args:
            filename: The name of the file to update tasks for.

        Returns:
            The updated task document.
        """
        system_design_doc = await self.repo.docs.system_design.get(filename)
        task_doc = await self.repo.docs.task.get(filename)
        if task_doc:
            task_doc = await self._merge(system_design_doc=system_design_doc, task_doc=task_doc)
            await self.repo.docs.task.save_doc(doc=task_doc, dependencies={system_design_doc.root_relative_path})
        else:
            rsp = await self._run_new_tasks(context=system_design_doc.content)
            task_doc = await self.repo.docs.task.save(
                filename=filename,
                content=rsp.instruct_content.model_dump_json(),
                dependencies={system_design_doc.root_relative_path},
            )
        await self._update_requirements(task_doc)
        return task_doc

    async def _run_new_tasks(self, context):
        """Generates new tasks based on the given context.

        This method uses the PM_NODE to fill in the context for new tasks and returns the generated node.

        Args:
            context: The context for generating new tasks.

        Returns:
            The generated node with new tasks.
        """
        node = await PM_NODE.fill(context, self.llm, schema=self.prompt_schema)
        return node

    async def _merge(self, system_design_doc, task_doc) -> Document:
        """Merges new requirements with existing tasks.

        This method formats the new requirements and existing tasks into a context, uses the REFINED_PM_NODE
        to fill in the context, and updates the task document with the merged content.

        Args:
            system_design_doc: The system design document containing new requirements.
            task_doc: The existing task document to merge with.

        Returns:
            The updated task document with merged content.
        """
        context = NEW_REQ_TEMPLATE.format(context=system_design_doc.content, old_task=task_doc.content)
        node = await REFINED_PM_NODE.fill(context, self.llm, schema=self.prompt_schema)
        task_doc.content = node.instruct_content.model_dump_json()
        return task_doc

    async def _update_requirements(self, doc):
        """Updates the requirements document based on the given task document.

        This method extracts required Python packages from the task document, updates the requirements document
        with these packages, and saves the updated requirements document.

        Args:
            doc: The task document to extract requirements from.
        """
        m = json.loads(doc.content)
        packages = set(m.get("Required Python packages", set()))
        requirement_doc = await self.repo.get(filename=PACKAGE_REQUIREMENTS_FILENAME)
        if not requirement_doc:
            requirement_doc = Document(filename=PACKAGE_REQUIREMENTS_FILENAME, root_path=".", content="")
        lines = requirement_doc.content.splitlines()
        for pkg in lines:
            if pkg == "":
                continue
            packages.add(pkg)
        await self.repo.save(filename=PACKAGE_REQUIREMENTS_FILENAME, content="\n".join(packages))
