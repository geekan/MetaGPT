#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/11 19:26
# @Author  : alexanderwu
# @File    : design_api.py
# @Modified By: mashenquan, 2023/11/27.
#             1. According to Section 2.2.3.1 of RFC 135, replace file data in the message with the file name.
#             2. According to the design in Section 2.2.3.5.3 of RFC 135, add incremental iteration functionality.
# @Modified By: mashenquan, 2023/12/5. Move the generation logic of the project name to WritePRD.

import json
from pathlib import Path
from typing import Optional

from metagpt.actions import Action, ActionOutput
from metagpt.actions.design_api_an import (
    DATA_STRUCTURES_AND_INTERFACES,
    DESIGN_API_NODE,
    PROGRAM_CALL_FLOW,
    REFINED_DATA_STRUCTURES_AND_INTERFACES,
    REFINED_DESIGN_NODE,
    REFINED_PROGRAM_CALL_FLOW,
)
from metagpt.const import DATA_API_DESIGN_FILE_REPO, SEQ_FLOW_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import Document, Documents, Message
from metagpt.utils.mermaid import mermaid_to_file

NEW_REQ_TEMPLATE = """
### Legacy Content
{old_design}

### New Requirements
{context}
"""


class WriteDesign(Action):
    """Handles the writing and updating of system design documents based on PRD changes.

    This class is responsible for detecting changes in PRD documents, updating system design documents accordingly,
    and saving new or updated design documents. It also handles the generation and saving of data API designs and
    sequence flow diagrams in mermaid format.

    Attributes:
        name: A string attribute.
        i_context: An optional string that provides context for the action.
        desc: A description of what the action does.
    """

    name: str = ""
    i_context: Optional[str] = None
    desc: str = (
        "Based on the PRD, think about the system design, and design the corresponding APIs, "
        "data structures, library tables, processes, and paths. Please provide your design, feedback "
        "clearly and in detail."
    )

    async def run(self, with_messages: Message, schema: str = None):
        """Executes the action to process changed PRD and system design documents.

        Args:
            with_messages: A Message object containing messages related to the action.
            schema: An optional string representing the schema to be used.

        Returns:
            An ActionOutput object containing the content of changed documents and instructions.
        """
        # Use `git status` to identify which PRD documents have been modified in the `docs/prd` directory.
        changed_prds = self.repo.docs.prd.changed_files
        # Use `git status` to identify which design documents in the `docs/system_designs` directory have undergone
        # changes.
        changed_system_designs = self.repo.docs.system_design.changed_files

        # For those PRDs and design documents that have undergone changes, regenerate the design content.
        changed_files = Documents()
        for filename in changed_prds.keys():
            doc = await self._update_system_design(filename=filename)
            changed_files.docs[filename] = doc

        for filename in changed_system_designs.keys():
            if filename in changed_files.docs:
                continue
            doc = await self._update_system_design(filename=filename)
            changed_files.docs[filename] = doc
        if not changed_files.docs:
            logger.info("Nothing has changed.")
        # Wait until all files under `docs/system_designs/` are processed before sending the publish message,
        # leaving room for global optimization in subsequent steps.
        return ActionOutput(content=changed_files.model_dump_json(), instruct_content=changed_files)

    async def _new_system_design(self, context):
        """Creates a new system design document based on the provided context.

        Args:
            context: A string containing the context or requirements for the new system design.

        Returns:
            A node representing the new system design.
        """
        node = await DESIGN_API_NODE.fill(context=context, llm=self.llm)
        return node

    async def _merge(self, prd_doc, system_design_doc):
        """Merges changes from a PRD document into an existing system design document.

        Args:
            prd_doc: The PRD document containing new requirements.
            system_design_doc: The existing system design document to be updated.

        Returns:
            The updated system design document.
        """
        context = NEW_REQ_TEMPLATE.format(old_design=system_design_doc.content, context=prd_doc.content)
        node = await REFINED_DESIGN_NODE.fill(context=context, llm=self.llm)
        system_design_doc.content = node.instruct_content.model_dump_json()
        return system_design_doc

    async def _update_system_design(self, filename) -> Document:
        """Updates or creates a system design document based on changes in the corresponding PRD document.

        Args:
            filename: The name of the file to be updated or created.

        Returns:
            The updated or newly created system design Document.
        """
        prd = await self.repo.docs.prd.get(filename)
        old_system_design_doc = await self.repo.docs.system_design.get(filename)
        if not old_system_design_doc:
            system_design = await self._new_system_design(context=prd.content)
            doc = await self.repo.docs.system_design.save(
                filename=filename,
                content=system_design.instruct_content.model_dump_json(),
                dependencies={prd.root_relative_path},
            )
        else:
            doc = await self._merge(prd_doc=prd, system_design_doc=old_system_design_doc)
            await self.repo.docs.system_design.save_doc(doc=doc, dependencies={prd.root_relative_path})
        await self._save_data_api_design(doc)
        await self._save_seq_flow(doc)
        await self.repo.resources.system_design.save_pdf(doc=doc)
        return doc

    async def _save_data_api_design(self, design_doc):
        """Saves the data API design part of a system design document as a mermaid file.

        Args:
            design_doc: The system design document containing the data API design.
        """
        m = json.loads(design_doc.content)
        data_api_design = m.get(DATA_STRUCTURES_AND_INTERFACES.key) or m.get(REFINED_DATA_STRUCTURES_AND_INTERFACES.key)
        if not data_api_design:
            return
        pathname = self.repo.workdir / DATA_API_DESIGN_FILE_REPO / Path(design_doc.filename).with_suffix("")
        await self._save_mermaid_file(data_api_design, pathname)
        logger.info(f"Save class view to {str(pathname)}")

    async def _save_seq_flow(self, design_doc):
        """Saves the sequence flow part of a system design document as a mermaid file.

        Args:
            design_doc: The system design document containing the sequence flow diagram.
        """
        m = json.loads(design_doc.content)
        seq_flow = m.get(PROGRAM_CALL_FLOW.key) or m.get(REFINED_PROGRAM_CALL_FLOW.key)
        if not seq_flow:
            return
        pathname = self.repo.workdir / Path(SEQ_FLOW_FILE_REPO) / Path(design_doc.filename).with_suffix("")
        await self._save_mermaid_file(seq_flow, pathname)
        logger.info(f"Saving sequence flow to {str(pathname)}")

    async def _save_mermaid_file(self, data: str, pathname: Path):
        """Saves a given data string as a mermaid file to the specified path.

        Args:
            data: The data string to be saved as a mermaid file.
            pathname: The Path object representing the file path where the mermaid file will be saved.
        """
        pathname.parent.mkdir(parents=True, exist_ok=True)
        await mermaid_to_file(self.config.mermaid_engine, data, pathname)
