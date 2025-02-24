#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_prd.py
@Modified By: mashenquan, 2023/11/27.
            1. According to Section 2.2.3.1 of RFC 135, replace file data in the message with the file name.
            2. According to the design in Section 2.2.3.5.2 of RFC 135, add incremental iteration functionality.
            3. Move the document storage operations related to WritePRD from the save operation of WriteDesign.
@Modified By: mashenquan, 2023/12/5. Move the generation logic of the project name to WritePRD.
"""

from __future__ import annotations

import json
from pathlib import Path

from metagpt.actions import Action, ActionOutput
from metagpt.actions.action_node import ActionNode
from metagpt.actions.fix_bug import FixBug
from metagpt.actions.write_prd_an import (
    COMPETITIVE_QUADRANT_CHART,
    PROJECT_NAME,
    REFINED_PRD_NODE,
    WP_IS_RELATIVE_NODE,
    WP_ISSUE_TYPE_NODE,
    WRITE_PRD_NODE,
)
from metagpt.const import (
    BUGFIX_FILENAME,
    COMPETITIVE_ANALYSIS_FILE_REPO,
    REQUIREMENT_FILENAME,
)
from metagpt.logs import logger
from metagpt.schema import BugFixContext, Document, Documents, Message
from metagpt.utils.common import CodeParser
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.mermaid import mermaid_to_file
from metagpt.utils.project_repo import ProjectRepo

CONTEXT_TEMPLATE = """
### Project Name
{project_name}

### Original Requirements
{requirements}

### Search Information
-
"""

NEW_REQ_TEMPLATE = """
### Legacy Content
{old_prd}

### New Requirements
{requirements}
"""


class WritePRD(Action):
    """WritePRD deal with the following situations:
    1. Bugfix: If the requirement is a bugfix, the bugfix document will be generated.
    2. New requirement: If the requirement is a new requirement, the PRD document will be generated.
    3. Requirement update: If the requirement is an update, the PRD document will be updated.
    """

    async def run(self, with_messages, *args, **kwargs) -> ActionOutput | Message:
        """Run the action."""
        repo = ProjectRepo(self.config.project_path)
        req: Document = await repo.requirement
        docs: list[Document] = await repo.docs.prd.get_all()
        if not req:
            raise FileNotFoundError("No requirement document found.")

        if await self._is_bugfix(req.content, repo=repo):
            logger.info(f"Bugfix detected: {req.content}")
            return await self._handle_bugfix(req, repo=repo)
        # remove bugfix file from last round in case of conflict
        await repo.docs.delete(filename=BUGFIX_FILENAME)

        # if requirement is related to other documents, update them, otherwise create a new one
        if related_docs := await self.get_related_docs(req, docs):
            logger.info(f"Requirement update detected: {req.content}")
            return await self._handle_requirement_update(req, related_docs, repo=repo)
        else:
            logger.info(f"New requirement detected: {req.content}")
            return await self._handle_new_requirement(req, repo=repo)

    async def _handle_bugfix(self, req: Document, repo: ProjectRepo) -> Message:
        # ... bugfix logic ...
        await repo.docs.save(filename=BUGFIX_FILENAME, content=req.content)
        await repo.docs.save(filename=REQUIREMENT_FILENAME, content="")
        bug_fix = BugFixContext(filename=BUGFIX_FILENAME)
        return Message(
            content=bug_fix.model_dump_json(),
            instruct_content=bug_fix,
            role="",
            cause_by=FixBug,
            sent_from=self,
            send_to="Alex",  # the name of Engineer
        )

    async def _handle_new_requirement(self, req: Document, repo: ProjectRepo) -> ActionOutput:
        """handle new requirement"""
        project_name = self.project_name
        context = CONTEXT_TEMPLATE.format(requirements=req, project_name=project_name)
        exclude = [PROJECT_NAME.key] if project_name else []
        node = await WRITE_PRD_NODE.fill(context=context, llm=self.llm, exclude=exclude)  # schema=schema
        await self._rename_workspace(node, repo=repo)
        new_prd_doc = await repo.docs.prd.save(
            filename=FileRepository.new_filename() + ".json", content=node.instruct_content.model_dump_json()
        )
        await self._save_competitive_analysis(new_prd_doc, repo=repo)
        await repo.resources.prd.save_pdf(doc=new_prd_doc)
        return Documents.from_iterable(documents=[new_prd_doc]).to_action_output()

    async def _handle_requirement_update(
        self, req: Document, related_docs: list[Document], repo: ProjectRepo
    ) -> ActionOutput:
        # ... requirement update logic ...
        for doc in related_docs:
            await self._update_prd(req, doc, repo=repo)
        return Documents.from_iterable(documents=related_docs).to_action_output()

    async def _is_bugfix(self, context: str, repo: ProjectRepo) -> bool:
        if not repo.code_files_exists():
            return False
        node = await WP_ISSUE_TYPE_NODE.fill(context, self.llm)
        return node.get("issue_type") == "BUG"

    async def get_related_docs(self, req: Document, docs: list[Document]) -> list[Document]:
        """get the related documents"""
        # refine: use gather to speed up
        return [i for i in docs if await self._is_related(req, i)]

    async def _is_related(self, req: Document, old_prd: Document) -> bool:
        context = NEW_REQ_TEMPLATE.format(old_prd=old_prd.content, requirements=req.content)
        node = await WP_IS_RELATIVE_NODE.fill(context, self.llm)
        return node.get("is_relative") == "YES"

    async def _merge(self, req: Document, related_doc: Document, repo: ProjectRepo) -> Document:
        if not self.project_name:
            self.project_name = Path(self.project_path).name
        prompt = NEW_REQ_TEMPLATE.format(requirements=req.content, old_prd=related_doc.content)
        node = await REFINED_PRD_NODE.fill(context=prompt, llm=self.llm, schema=self.prompt_schema)
        related_doc.content = node.instruct_content.model_dump_json()
        await self._rename_workspace(node, repo=repo)
        return related_doc

    async def _update_prd(self, req: Document, prd_doc: Document, repo: ProjectRepo) -> Document:
        new_prd_doc: Document = await self._merge(req, prd_doc, repo=repo)
        await repo.docs.prd.save_doc(doc=new_prd_doc)
        await self._save_competitive_analysis(new_prd_doc, repo=repo)
        await repo.resources.prd.save_pdf(doc=new_prd_doc)
        return new_prd_doc

    async def _save_competitive_analysis(self, prd_doc: Document, repo: ProjectRepo):
        m = json.loads(prd_doc.content)
        quadrant_chart = m.get(COMPETITIVE_QUADRANT_CHART.key)
        if not quadrant_chart:
            return
        pathname = repo.workdir / COMPETITIVE_ANALYSIS_FILE_REPO / Path(prd_doc.filename).stem
        pathname.parent.mkdir(parents=True, exist_ok=True)
        await mermaid_to_file(self.config.mermaid.engine, quadrant_chart, pathname)

    async def _rename_workspace(self, prd, repo: ProjectRepo):
        if not self.project_name:
            if isinstance(prd, (ActionOutput, ActionNode)):
                ws_name = prd.instruct_content.model_dump()["Project Name"]
            else:
                ws_name = CodeParser.parse_str(block="Project Name", text=prd)
            if ws_name:
                self.project_name = ws_name
        repo.git_repo.rename_root(self.project_name)
