#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:26
@Author  : alexanderwu
@File    : design_api.py
@Modified By: mashenquan, 2023/11/27.
            1. According to Section 2.2.3.1 of RFC 135, replace file data in the message with the file name.
            2. According to the design in Section 2.2.3.5.3 of RFC 135, add incremental iteration functionality.
@Modified By: mashenquan, 2023/12/5. Move the generation logic of the project name to WritePRD.
"""
import json
from pathlib import Path
from typing import Optional

from metagpt.actions import Action, ActionOutput
from metagpt.actions.design_api_an import DESIGN_API_NODE
from metagpt.config import CONFIG
from metagpt.const import (
    DATA_API_DESIGN_FILE_REPO,
    PRDS_FILE_REPO,
    SEQ_FLOW_FILE_REPO,
    SYSTEM_DESIGN_FILE_REPO,
    SYSTEM_DESIGN_PDF_FILE_REPO,
)
from metagpt.logs import logger
from metagpt.schema import Document, Documents, Message
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.mermaid import mermaid_to_file

NEW_REQ_TEMPLATE = """
### Legacy Content
{old_design}

### New Requirements
{context}
"""


class WriteDesign(Action):
    name: str = ""
    context: Optional[str] = None
    desc: str = (
        "Based on the PRD, think about the system design, and design the corresponding APIs, "
        "data structures, library tables, processes, and paths. Please provide your design, feedback "
        "clearly and in detail."
    )

    async def run(self, with_messages: Message, schema: str = CONFIG.prompt_schema):
        # Use `git status` to identify which PRD documents have been modified in the `docs/prds` directory.
        prds_file_repo = CONFIG.git_repo.new_file_repository(PRDS_FILE_REPO)
        changed_prds = prds_file_repo.changed_files
        # Use `git status` to identify which design documents in the `docs/system_designs` directory have undergone
        # changes.
        system_design_file_repo = CONFIG.git_repo.new_file_repository(SYSTEM_DESIGN_FILE_REPO)
        changed_system_designs = system_design_file_repo.changed_files

        # For those PRDs and design documents that have undergone changes, regenerate the design content.
        changed_files = Documents()
        for filename in changed_prds.keys():
            doc = await self._update_system_design(
                filename=filename, prds_file_repo=prds_file_repo, system_design_file_repo=system_design_file_repo
            )
            changed_files.docs[filename] = doc

        for filename in changed_system_designs.keys():
            if filename in changed_files.docs:
                continue
            doc = await self._update_system_design(
                filename=filename, prds_file_repo=prds_file_repo, system_design_file_repo=system_design_file_repo
            )
            changed_files.docs[filename] = doc
        if not changed_files.docs:
            logger.info("Nothing has changed.")
        # Wait until all files under `docs/system_designs/` are processed before sending the publish message,
        # leaving room for global optimization in subsequent steps.
        return ActionOutput(content=changed_files.model_dump_json(), instruct_content=changed_files)

    async def _new_system_design(self, context, schema=CONFIG.prompt_schema):
        node = await DESIGN_API_NODE.fill(context=context, llm=self.llm, schema=schema)
        return node

    async def _merge(self, prd_doc, system_design_doc, schema=CONFIG.prompt_schema):
        context = NEW_REQ_TEMPLATE.format(old_design=system_design_doc.content, context=prd_doc.content)
        node = await DESIGN_API_NODE.fill(context=context, llm=self.llm, schema=schema)
        system_design_doc.content = node.instruct_content.model_dump_json()
        return system_design_doc

    async def _update_system_design(self, filename, prds_file_repo, system_design_file_repo) -> Document:
        prd = await prds_file_repo.get(filename)
        old_system_design_doc = await system_design_file_repo.get(filename)
        if not old_system_design_doc:
            system_design = await self._new_system_design(context=prd.content)
            doc = Document(
                root_path=SYSTEM_DESIGN_FILE_REPO,
                filename=filename,
                content=system_design.instruct_content.model_dump_json(),
            )
        else:
            doc = await self._merge(prd_doc=prd, system_design_doc=old_system_design_doc)
        await system_design_file_repo.save(
            filename=filename, content=doc.content, dependencies={prd.root_relative_path}
        )
        await self._save_data_api_design(doc)
        await self._save_seq_flow(doc)
        await self._save_pdf(doc)
        return doc

    @staticmethod
    async def _save_data_api_design(design_doc):
        m = json.loads(design_doc.content)
        data_api_design = m.get("Data structures and interfaces")
        if not data_api_design:
            return
        pathname = CONFIG.git_repo.workdir / DATA_API_DESIGN_FILE_REPO / Path(design_doc.filename).with_suffix("")
        await WriteDesign._save_mermaid_file(data_api_design, pathname)
        logger.info(f"Save class view to {str(pathname)}")

    @staticmethod
    async def _save_seq_flow(design_doc):
        m = json.loads(design_doc.content)
        seq_flow = m.get("Program call flow")
        if not seq_flow:
            return
        pathname = CONFIG.git_repo.workdir / Path(SEQ_FLOW_FILE_REPO) / Path(design_doc.filename).with_suffix("")
        await WriteDesign._save_mermaid_file(seq_flow, pathname)
        logger.info(f"Saving sequence flow to {str(pathname)}")

    @staticmethod
    async def _save_pdf(design_doc):
        await FileRepository.save_as(doc=design_doc, with_suffix=".md", relative_path=SYSTEM_DESIGN_PDF_FILE_REPO)

    @staticmethod
    async def _save_mermaid_file(data: str, pathname: Path):
        pathname.parent.mkdir(parents=True, exist_ok=True)
        await mermaid_to_file(data, pathname)
