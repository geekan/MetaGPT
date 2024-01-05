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
import uuid
from pathlib import Path
from typing import Optional

from metagpt.actions import Action, ActionOutput
from metagpt.actions.action_node import ActionNode
from metagpt.actions.fix_bug import FixBug
from metagpt.actions.write_prd_an import (
    PROJECT_NAME,
    WP_IS_RELATIVE_NODE,
    WP_ISSUE_TYPE_NODE,
    WRITE_PRD_NODE,
)
from metagpt.config import CONFIG
from metagpt.const import (
    BUGFIX_FILENAME,
    COMPETITIVE_ANALYSIS_FILE_REPO,
    DOCS_FILE_REPO,
    PRD_PDF_FILE_REPO,
    PRDS_FILE_REPO,
    REQUIREMENT_FILENAME,
)
from metagpt.logs import logger
from metagpt.schema import BugFixContext, Document, Documents, Message
from metagpt.utils.common import CodeParser
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.mermaid import mermaid_to_file

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
    name: str = "WritePRD"
    content: Optional[str] = None

    async def run(self, with_messages, schema=CONFIG.prompt_schema, *args, **kwargs) -> ActionOutput | Message:
        # Determine which requirement documents need to be rewritten: Use LLM to assess whether new requirements are
        # related to the PRD. If they are related, rewrite the PRD.
        docs_file_repo = CONFIG.git_repo.new_file_repository(relative_path=DOCS_FILE_REPO)
        requirement_doc = await docs_file_repo.get(filename=REQUIREMENT_FILENAME)
        if requirement_doc and await self._is_bugfix(requirement_doc.content):
            await docs_file_repo.save(filename=BUGFIX_FILENAME, content=requirement_doc.content)
            await docs_file_repo.save(filename=REQUIREMENT_FILENAME, content="")
            bug_fix = BugFixContext(filename=BUGFIX_FILENAME)
            return Message(
                content=bug_fix.model_dump_json(),
                instruct_content=bug_fix,
                role="",
                cause_by=FixBug,
                sent_from=self,
                send_to="Alex",  # the name of Engineer
            )
        else:
            await docs_file_repo.delete(filename=BUGFIX_FILENAME)

        prds_file_repo = CONFIG.git_repo.new_file_repository(PRDS_FILE_REPO)
        prd_docs = await prds_file_repo.get_all()
        change_files = Documents()
        for prd_doc in prd_docs:
            prd_doc = await self._update_prd(
                requirement_doc=requirement_doc, prd_doc=prd_doc, prds_file_repo=prds_file_repo, *args, **kwargs
            )
            if not prd_doc:
                continue
            change_files.docs[prd_doc.filename] = prd_doc
            logger.info(f"rewrite prd: {prd_doc.filename}")
        # If there is no existing PRD, generate one using 'docs/requirement.txt'.
        if not change_files.docs:
            prd_doc = await self._update_prd(
                requirement_doc=requirement_doc, prd_doc=None, prds_file_repo=prds_file_repo, *args, **kwargs
            )
            if prd_doc:
                change_files.docs[prd_doc.filename] = prd_doc
                logger.debug(f"new prd: {prd_doc.filename}")
        # Once all files under 'docs/prds/' have been compared with the newly added requirements, trigger the
        # 'publish' message to transition the workflow to the next stage. This design allows room for global
        # optimization in subsequent steps.
        return ActionOutput(content=change_files.model_dump_json(), instruct_content=change_files)

    async def _run_new_requirement(self, requirements, schema=CONFIG.prompt_schema) -> ActionOutput:
        # sas = SearchAndSummarize()
        # # rsp = await sas.run(context=requirements, system_text=SEARCH_AND_SUMMARIZE_SYSTEM_EN_US)
        # rsp = ""
        # info = f"### Search Results\n{sas.result}\n\n### Search Summary\n{rsp}"
        # if sas.result:
        #     logger.info(sas.result)
        #     logger.info(rsp)
        project_name = CONFIG.project_name or ""
        context = CONTEXT_TEMPLATE.format(requirements=requirements, project_name=project_name)
        exclude = [PROJECT_NAME.key] if project_name else []
        node = await WRITE_PRD_NODE.fill(context=context, llm=self.llm, exclude=exclude)  # schema=schema
        await self._rename_workspace(node)
        return node

    async def _is_relative(self, new_requirement_doc, old_prd_doc) -> bool:
        context = NEW_REQ_TEMPLATE.format(old_prd=old_prd_doc.content, requirements=new_requirement_doc.content)
        node = await WP_IS_RELATIVE_NODE.fill(context, self.llm)
        return node.get("is_relative") == "YES"

    async def _merge(self, new_requirement_doc, prd_doc, schema=CONFIG.prompt_schema) -> Document:
        if not CONFIG.project_name:
            CONFIG.project_name = Path(CONFIG.project_path).name
        prompt = NEW_REQ_TEMPLATE.format(requirements=new_requirement_doc.content, old_prd=prd_doc.content)
        node = await WRITE_PRD_NODE.fill(context=prompt, llm=self.llm, schema=schema)
        prd_doc.content = node.instruct_content.model_dump_json()
        await self._rename_workspace(node)
        return prd_doc

    async def _update_prd(self, requirement_doc, prd_doc, prds_file_repo, *args, **kwargs) -> Document | None:
        if not prd_doc:
            prd = await self._run_new_requirement(
                requirements=[requirement_doc.content if requirement_doc else ""], *args, **kwargs
            )
            new_prd_doc = Document(
                root_path=PRDS_FILE_REPO,
                filename=FileRepository.new_filename() + ".json",
                content=prd.instruct_content.model_dump_json(),
            )
        elif await self._is_relative(requirement_doc, prd_doc):
            new_prd_doc = await self._merge(requirement_doc, prd_doc)
        else:
            return None
        await prds_file_repo.save(filename=new_prd_doc.filename, content=new_prd_doc.content)
        await self._save_competitive_analysis(new_prd_doc)
        await self._save_pdf(new_prd_doc)
        return new_prd_doc

    @staticmethod
    async def _save_competitive_analysis(prd_doc):
        m = json.loads(prd_doc.content)
        quadrant_chart = m.get("Competitive Quadrant Chart")
        if not quadrant_chart:
            return
        pathname = (
            CONFIG.git_repo.workdir / Path(COMPETITIVE_ANALYSIS_FILE_REPO) / Path(prd_doc.filename).with_suffix("")
        )
        if not pathname.parent.exists():
            pathname.parent.mkdir(parents=True, exist_ok=True)
        await mermaid_to_file(quadrant_chart, pathname)

    @staticmethod
    async def _save_pdf(prd_doc):
        await FileRepository.save_as(doc=prd_doc, with_suffix=".md", relative_path=PRD_PDF_FILE_REPO)

    @staticmethod
    async def _rename_workspace(prd):
        if not CONFIG.project_name:
            if isinstance(prd, (ActionOutput, ActionNode)):
                ws_name = prd.instruct_content.model_dump()["Project Name"]
            else:
                ws_name = CodeParser.parse_str(block="Project Name", text=prd)
            if ws_name:
                CONFIG.project_name = ws_name
        if not CONFIG.project_name:  # The LLM failed to provide a project name, and the user didn't provide one either.
            CONFIG.project_name = "app" + uuid.uuid4().hex[:16]
        CONFIG.git_repo.rename_root(CONFIG.project_name)

    async def _is_bugfix(self, context) -> bool:
        src_workspace_path = CONFIG.git_repo.workdir / CONFIG.git_repo.workdir.name
        code_files = CONFIG.git_repo.get_files(relative_path=src_workspace_path)
        if not code_files:
            return False
        node = await WP_ISSUE_TYPE_NODE.fill(context, self.llm)
        return node.get("issue_type") == "BUG"
