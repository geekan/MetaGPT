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
@Modified By: mashenquan, 2024/5/31. Implement Chapter 3 of RFC 236.
"""
import json
from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel, Field

from metagpt.actions import Action
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
from metagpt.schema import AIMessage, Document, Documents, Message
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import (
    aread,
    awrite,
    rectify_pathname,
    save_json_to_markdown,
    to_markdown_code_block,
)
from metagpt.utils.mermaid import mermaid_to_file
from metagpt.utils.project_repo import ProjectRepo
from metagpt.utils.report import DocsReporter, GalleryReporter

NEW_REQ_TEMPLATE = """
### Legacy Content
{old_design}

### New Requirements
{context}
"""


@register_tool(include_functions=["run"])
class WriteDesign(Action):
    name: str = ""
    i_context: Optional[str] = None
    desc: str = (
        "Based on the PRD, think about the system design, and design the corresponding APIs, "
        "data structures, library tables, processes, and paths. Please provide your design, feedback "
        "clearly and in detail."
    )
    repo: Optional[ProjectRepo] = Field(default=None, exclude=True)
    input_args: Optional[BaseModel] = Field(default=None, exclude=True)

    async def run(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        prd_filename: str = "",
        legacy_design_filename: str = "",
        extra_info: str = "",
        output_pathname: str = "",
        **kwargs,
    ) -> Union[AIMessage, str]:
        """
        Write a system design.

        Args:
            user_requirement (str): The user's requirements for the system design.
            prd_filename (str, optional): The filename of the Product Requirement Document (PRD).
            legacy_design_filename (str, optional): The filename of the legacy design document.
            extra_info (str, optional): Additional information to be included in the system design.
            output_pathname (str, optional): The output file path of the document.

        Returns:
            str: The file path of the generated system design.

        Example:
            # Write a new system design and save to the path name.
            >>> user_requirement = "Write system design for a snake game"
            >>> extra_info = "Your extra information"
            >>> output_pathname = "snake_game/docs/system_design.json"
            >>> action = WriteDesign()
            >>> result = await action.run(user_requirement=user_requirement, extra_info=extra_info, output_pathname=output_pathname)
            >>> print(result)
            System Design filename: "/absolute/path/to/snake_game/docs/system_design.json"

            # Rewrite an existing system design and save to the path name.
            >>> user_requirement = "Write system design for a snake game, include new features such as a web UI"
            >>> extra_info = "Your extra information"
            >>> legacy_design_filename = "/absolute/path/to/snake_game/docs/system_design.json"
            >>> output_pathname = "/absolute/path/to/snake_game/docs/system_design_new.json"
            >>> action = WriteDesign()
            >>> result = await action.run(user_requirement=user_requirement, extra_info=extra_info, legacy_design_filename=legacy_design_filename, output_pathname=output_pathname)
            >>> print(result)
            System Design filename: "/absolute/path/to/snake_game/docs/system_design_new.json"

            # Write a new system design with the given PRD(Product Requirement Document) and save to the path name.
            >>> user_requirement = "Write system design for a snake game based on the PRD at /absolute/path/to/snake_game/docs/prd.json"
            >>> extra_info = "Your extra information"
            >>> prd_filename = "/absolute/path/to/snake_game/docs/prd.json"
            >>> output_pathname = "/absolute/path/to/snake_game/docs/sytem_design.json"
            >>> action = WriteDesign()
            >>> result = await action.run(user_requirement=user_requirement, extra_info=extra_info, prd_filename=prd_filename, output_pathname=output_pathname)
            >>> print(result)
            System Design filename: "/absolute/path/to/snake_game/docs/sytem_design.json"

            # Rewrite an existing system design with the given PRD(Product Requirement Document) and save to the path name.
            >>> user_requirement = "Write system design for a snake game, include new features such as a web UI"
            >>> extra_info = "Your extra information"
            >>> prd_filename = "/absolute/path/to/snake_game/docs/prd.json"
            >>> legacy_design_filename = "/absolute/path/to/snake_game/docs/system_design.json"
            >>> output_pathname = "/absolute/path/to/snake_game/docs/system_design_new.json"
            >>> action = WriteDesign()
            >>> result = await action.run(user_requirement=user_requirement, extra_info=extra_info, prd_filename=prd_filename, legacy_design_filename=legacy_design_filename, output_pathname=output_pathname)
            >>> print(result)
            System Design filename: "/absolute/path/to/snake_game/docs/system_design_new.json"
        """
        if not with_messages:
            return await self._execute_api(
                user_requirement=user_requirement,
                prd_filename=prd_filename,
                legacy_design_filename=legacy_design_filename,
                extra_info=extra_info,
                output_pathname=output_pathname,
            )

        self.input_args = with_messages[-1].instruct_content
        self.repo = ProjectRepo(self.input_args.project_path)
        changed_prds = self.input_args.changed_prd_filenames
        changed_system_designs = [
            str(self.repo.docs.system_design.workdir / i)
            for i in list(self.repo.docs.system_design.changed_files.keys())
        ]

        # For those PRDs and design documents that have undergone changes, regenerate the design content.
        changed_files = Documents()
        for filename in changed_prds:
            doc = await self._update_system_design(filename=filename)
            changed_files.docs[filename] = doc

        for filename in changed_system_designs:
            if filename in changed_files.docs:
                continue
            doc = await self._update_system_design(filename=filename)
            changed_files.docs[filename] = doc
        if not changed_files.docs:
            logger.info("Nothing has changed.")
        # Wait until all files under `docs/system_designs/` are processed before sending the publish message,
        # leaving room for global optimization in subsequent steps.
        kvs = self.input_args.model_dump()
        kvs["changed_system_design_filenames"] = [
            str(self.repo.docs.system_design.workdir / i)
            for i in list(self.repo.docs.system_design.changed_files.keys())
        ]
        return AIMessage(
            content="Designing is complete. "
            + "\n".join(
                list(self.repo.docs.system_design.changed_files.keys())
                + list(self.repo.resources.data_api_design.changed_files.keys())
                + list(self.repo.resources.seq_flow.changed_files.keys())
            ),
            instruct_content=AIMessage.create_instruct_value(kvs=kvs, class_name="WriteDesignOutput"),
            cause_by=self,
        )

    async def _new_system_design(self, context):
        node = await DESIGN_API_NODE.fill(req=context, llm=self.llm, schema=self.prompt_schema)
        return node

    async def _merge(self, prd_doc, system_design_doc):
        context = NEW_REQ_TEMPLATE.format(old_design=system_design_doc.content, context=prd_doc.content)
        node = await REFINED_DESIGN_NODE.fill(req=context, llm=self.llm, schema=self.prompt_schema)
        system_design_doc.content = node.instruct_content.model_dump_json()
        return system_design_doc

    async def _update_system_design(self, filename) -> Document:
        root_relative_path = Path(filename).relative_to(self.repo.workdir)
        prd = await Document.load(filename=filename, project_path=self.repo.workdir)
        old_system_design_doc = await self.repo.docs.system_design.get(root_relative_path.name)
        async with DocsReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "design"}, "meta")
            if not old_system_design_doc:
                system_design = await self._new_system_design(context=prd.content)
                doc = await self.repo.docs.system_design.save(
                    filename=prd.filename,
                    content=system_design.instruct_content.model_dump_json(),
                    dependencies={prd.root_relative_path},
                )
            else:
                doc = await self._merge(prd_doc=prd, system_design_doc=old_system_design_doc)
                await self.repo.docs.system_design.save_doc(doc=doc, dependencies={prd.root_relative_path})
            await self._save_data_api_design(doc)
            await self._save_seq_flow(doc)
            md = await self.repo.resources.system_design.save_pdf(doc=doc)
            await reporter.async_report(self.repo.workdir / md.root_relative_path, "path")
        return doc

    async def _save_data_api_design(self, design_doc, output_filename: Path = None):
        m = json.loads(design_doc.content)
        data_api_design = m.get(DATA_STRUCTURES_AND_INTERFACES.key) or m.get(REFINED_DATA_STRUCTURES_AND_INTERFACES.key)
        if not data_api_design:
            return
        pathname = output_filename or self.repo.workdir / DATA_API_DESIGN_FILE_REPO / Path(
            design_doc.filename
        ).with_suffix("")
        await self._save_mermaid_file(data_api_design, pathname)
        logger.info(f"Save class view to {str(pathname)}")

    async def _save_seq_flow(self, design_doc, output_filename: Path = None):
        m = json.loads(design_doc.content)
        seq_flow = m.get(PROGRAM_CALL_FLOW.key) or m.get(REFINED_PROGRAM_CALL_FLOW.key)
        if not seq_flow:
            return
        pathname = output_filename or self.repo.workdir / Path(SEQ_FLOW_FILE_REPO) / Path(
            design_doc.filename
        ).with_suffix("")
        await self._save_mermaid_file(seq_flow, pathname)
        logger.info(f"Saving sequence flow to {str(pathname)}")

    async def _save_mermaid_file(self, data: str, pathname: Path):
        pathname.parent.mkdir(parents=True, exist_ok=True)
        await mermaid_to_file(self.config.mermaid.engine, data, pathname)
        image_path = pathname.parent / f"{pathname.name}.svg"
        if image_path.exists():
            await GalleryReporter().async_report(image_path, "path")

    async def _execute_api(
        self,
        user_requirement: str = "",
        prd_filename: str = "",
        legacy_design_filename: str = "",
        extra_info: str = "",
        output_pathname: str = "",
    ) -> str:
        prd_content = ""
        if prd_filename:
            prd_filename = rectify_pathname(path=prd_filename, default_filename="prd.json")
            prd_content = await aread(filename=prd_filename)
        context = "### User Requirements\n{user_requirement}\n### Extra_info\n{extra_info}\n### PRD\n{prd}\n".format(
            user_requirement=to_markdown_code_block(user_requirement),
            extra_info=to_markdown_code_block(extra_info),
            prd=to_markdown_code_block(prd_content),
        )
        async with DocsReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "design"}, "meta")
            if not legacy_design_filename:
                node = await self._new_system_design(context=context)
                design = Document(content=node.instruct_content.model_dump_json())
            else:
                old_design_content = await aread(filename=legacy_design_filename)
                design = await self._merge(
                    prd_doc=Document(content=context), system_design_doc=Document(content=old_design_content)
                )

            if not output_pathname:
                output_pathname = Path(output_pathname) / "docs" / "system_design.json"
            elif not Path(output_pathname).is_absolute():
                output_pathname = self.config.workspace.path / output_pathname
            output_pathname = rectify_pathname(path=output_pathname, default_filename="system_design.json")
            await awrite(filename=output_pathname, data=design.content)
            output_filename = output_pathname.parent / f"{output_pathname.stem}-class-diagram"
            await self._save_data_api_design(design_doc=design, output_filename=output_filename)
            output_filename = output_pathname.parent / f"{output_pathname.stem}-sequence-diagram"
            await self._save_seq_flow(design_doc=design, output_filename=output_filename)
            md_output_filename = output_pathname.with_suffix(".md")
            await save_json_to_markdown(content=design.content, output_filename=md_output_filename)
            await reporter.async_report(md_output_filename, "path")
        return f'System Design filename: "{str(output_pathname)}". \n The System Design has been completed.'
