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
@Modified By: mashenquan, 2024/5/31. Implement Chapter 3 of RFC 236.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel, Field

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
from metagpt.schema import AIMessage, Document, Documents, Message
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import (
    CodeParser,
    aread,
    awrite,
    rectify_pathname,
    save_json_to_markdown,
    to_markdown_code_block,
)
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.mermaid import mermaid_to_file
from metagpt.utils.project_repo import ProjectRepo
from metagpt.utils.report import DocsReporter, GalleryReporter

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


@register_tool(include_functions=["run"])
class WritePRD(Action):
    """WritePRD deal with the following situations:
    1. Bugfix: If the requirement is a bugfix, the bugfix document will be generated.
    2. New requirement: If the requirement is a new requirement, the PRD document will be generated.
    3. Requirement update: If the requirement is an update, the PRD document will be updated.
    """

    repo: Optional[ProjectRepo] = Field(default=None, exclude=True)
    input_args: Optional[BaseModel] = Field(default=None, exclude=True)

    async def run(
        self,
        with_messages: List[Message] = None,
        *,
        user_requirement: str = "",
        output_pathname: str = "",
        legacy_prd_filename: str = "",
        extra_info: str = "",
        **kwargs,
    ) -> Union[AIMessage, str]:
        """
        Write a Product Requirement Document.

        Args:
            user_requirement (str): A string detailing the user's requirements.
            output_pathname (str, optional): The output file path of the document. Defaults to "".
            legacy_prd_filename (str, optional): The file path of the legacy Product Requirement Document to use as a reference. Defaults to "".
            extra_info (str, optional): Additional information to include in the document. Defaults to "".
            **kwargs: Additional keyword arguments.

        Returns:
            str: The file path of the generated Product Requirement Document.

        Example:
            # Write a new PRD (Product Requirement Document)
            >>> user_requirement = "Write a snake game"
            >>> output_pathname = "snake_game/docs/prd.json"
            >>> extra_info = "YOUR EXTRA INFO, if any"
            >>> write_prd = WritePRD()
            >>> result = await write_prd.run(user_requirement=user_requirement, output_pathname=output_pathname, extra_info=extra_info)
            >>> print(result)
            PRD filename: "/absolute/path/to/snake_game/docs/prd.json"

            # Rewrite an existing PRD (Product Requirement Document) and save to a new path.
            >>> user_requirement = "Write PRD for a snake game, include new features such as a web UI"
            >>> legacy_prd_filename = "/absolute/path/to/snake_game/docs/prd.json"
            >>> output_pathname = "/absolute/path/to/snake_game/docs/prd_new.json"
            >>> extra_info = "YOUR EXTRA INFO, if any"
            >>> write_prd = WritePRD()
            >>> result = await write_prd.run(user_requirement=user_requirement, legacy_prd_filename=legacy_prd_filename, extra_info=extra_info)
            >>> print(result)
            PRD filename: "/absolute/path/to/snake_game/docs/prd_new.json"
        """
        if not with_messages:
            return await self._execute_api(
                user_requirement=user_requirement,
                output_pathname=output_pathname,
                legacy_prd_filename=legacy_prd_filename,
                extra_info=extra_info,
            )

        self.input_args = with_messages[-1].instruct_content
        if not self.input_args:
            self.repo = ProjectRepo(self.context.kwargs.project_path)
            await self.repo.docs.save(filename=REQUIREMENT_FILENAME, content=with_messages[-1].content)
            self.input_args = AIMessage.create_instruct_value(
                kvs={
                    "project_path": self.context.kwargs.project_path,
                    "requirements_filename": str(self.repo.docs.workdir / REQUIREMENT_FILENAME),
                    "prd_filenames": [str(self.repo.docs.prd.workdir / i) for i in self.repo.docs.prd.all_files],
                },
                class_name="PrepareDocumentsOutput",
            )
        else:
            self.repo = ProjectRepo(self.input_args.project_path)
        req = await Document.load(filename=self.input_args.requirements_filename)
        docs: list[Document] = [
            await Document.load(filename=i, project_path=self.repo.workdir) for i in self.input_args.prd_filenames
        ]

        if not req:
            raise FileNotFoundError("No requirement document found.")

        if await self._is_bugfix(req.content):
            logger.info(f"Bugfix detected: {req.content}")
            return await self._handle_bugfix(req)
        # remove bugfix file from last round in case of conflict
        await self.repo.docs.delete(filename=BUGFIX_FILENAME)

        # if requirement is related to other documents, update them, otherwise create a new one
        if related_docs := await self.get_related_docs(req, docs):
            logger.info(f"Requirement update detected: {req.content}")
            await self._handle_requirement_update(req=req, related_docs=related_docs)
        else:
            logger.info(f"New requirement detected: {req.content}")
            await self._handle_new_requirement(req)

        kvs = self.input_args.model_dump()
        kvs["changed_prd_filenames"] = [
            str(self.repo.docs.prd.workdir / i) for i in list(self.repo.docs.prd.changed_files.keys())
        ]
        kvs["project_path"] = str(self.repo.workdir)
        kvs["requirements_filename"] = str(self.repo.docs.workdir / REQUIREMENT_FILENAME)
        self.context.kwargs.project_path = str(self.repo.workdir)
        return AIMessage(
            content="PRD is completed. "
            + "\n".join(
                list(self.repo.docs.prd.changed_files.keys())
                + list(self.repo.resources.prd.changed_files.keys())
                + list(self.repo.resources.competitive_analysis.changed_files.keys())
            ),
            instruct_content=AIMessage.create_instruct_value(kvs=kvs, class_name="WritePRDOutput"),
            cause_by=self,
        )

    async def _handle_bugfix(self, req: Document) -> AIMessage:
        # ... bugfix logic ...
        await self.repo.docs.save(filename=BUGFIX_FILENAME, content=req.content)
        await self.repo.docs.save(filename=REQUIREMENT_FILENAME, content="")
        return AIMessage(
            content=f"A new issue is received: {BUGFIX_FILENAME}",
            cause_by=FixBug,
            instruct_content=AIMessage.create_instruct_value(
                {
                    "project_path": str(self.repo.workdir),
                    "issue_filename": str(self.repo.docs.workdir / BUGFIX_FILENAME),
                    "requirements_filename": str(self.repo.docs.workdir / REQUIREMENT_FILENAME),
                },
                class_name="IssueDetail",
            ),
            send_to="Alex",  # the name of Engineer
        )

    async def _new_prd(self, requirement: str) -> ActionNode:
        project_name = self.project_name
        context = CONTEXT_TEMPLATE.format(requirements=requirement, project_name=project_name)
        exclude = [PROJECT_NAME.key] if project_name else []
        node = await WRITE_PRD_NODE.fill(
            req=context, llm=self.llm, exclude=exclude, schema=self.prompt_schema
        )  # schema=schema
        return node

    async def _handle_new_requirement(self, req: Document) -> ActionOutput:
        """handle new requirement"""
        async with DocsReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "prd"}, "meta")
            node = await self._new_prd(req.content)
            await self._rename_workspace(node)
            new_prd_doc = await self.repo.docs.prd.save(
                filename=FileRepository.new_filename() + ".json", content=node.instruct_content.model_dump_json()
            )
            await self._save_competitive_analysis(new_prd_doc)
            md = await self.repo.resources.prd.save_pdf(doc=new_prd_doc)
            await reporter.async_report(self.repo.workdir / md.root_relative_path, "path")
            return Documents.from_iterable(documents=[new_prd_doc]).to_action_output()

    async def _handle_requirement_update(self, req: Document, related_docs: list[Document]) -> ActionOutput:
        # ... requirement update logic ...
        for doc in related_docs:
            await self._update_prd(req=req, prd_doc=doc)
        return Documents.from_iterable(documents=related_docs).to_action_output()

    async def _is_bugfix(self, context: str) -> bool:
        if not self.repo.code_files_exists():
            return False
        node = await WP_ISSUE_TYPE_NODE.fill(req=context, llm=self.llm)
        return node.get("issue_type") == "BUG"

    async def get_related_docs(self, req: Document, docs: list[Document]) -> list[Document]:
        """get the related documents"""
        # refine: use gather to speed up
        return [i for i in docs if await self._is_related(req, i)]

    async def _is_related(self, req: Document, old_prd: Document) -> bool:
        context = NEW_REQ_TEMPLATE.format(old_prd=old_prd.content, requirements=req.content)
        node = await WP_IS_RELATIVE_NODE.fill(req=context, llm=self.llm)
        return node.get("is_relative") == "YES"

    async def _merge(self, req: Document, related_doc: Document) -> Document:
        if not self.project_name:
            self.project_name = Path(self.project_path).name
        prompt = NEW_REQ_TEMPLATE.format(requirements=req.content, old_prd=related_doc.content)
        node = await REFINED_PRD_NODE.fill(req=prompt, llm=self.llm, schema=self.prompt_schema)
        related_doc.content = node.instruct_content.model_dump_json()
        await self._rename_workspace(node)
        return related_doc

    async def _update_prd(self, req: Document, prd_doc: Document) -> Document:
        async with DocsReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "prd"}, "meta")
            new_prd_doc: Document = await self._merge(req=req, related_doc=prd_doc)
            await self.repo.docs.prd.save_doc(doc=new_prd_doc)
            await self._save_competitive_analysis(new_prd_doc)
            md = await self.repo.resources.prd.save_pdf(doc=new_prd_doc)
            await reporter.async_report(self.repo.workdir / md.root_relative_path, "path")
        return new_prd_doc

    async def _save_competitive_analysis(self, prd_doc: Document, output_filename: Path = None):
        m = json.loads(prd_doc.content)
        quadrant_chart = m.get(COMPETITIVE_QUADRANT_CHART.key)
        if not quadrant_chart:
            return
        pathname = output_filename or self.repo.workdir / COMPETITIVE_ANALYSIS_FILE_REPO / Path(prd_doc.filename).stem
        pathname.parent.mkdir(parents=True, exist_ok=True)
        await mermaid_to_file(self.config.mermaid.engine, quadrant_chart, pathname)
        image_path = pathname.parent / f"{pathname.name}.svg"
        if image_path.exists():
            await GalleryReporter().async_report(image_path, "path")

    async def _rename_workspace(self, prd):
        if not self.project_name:
            if isinstance(prd, (ActionOutput, ActionNode)):
                ws_name = prd.instruct_content.model_dump()["Project Name"]
            else:
                ws_name = CodeParser.parse_str(block="Project Name", text=prd)
            if ws_name:
                self.project_name = ws_name
        if self.repo:
            self.repo.git_repo.rename_root(self.project_name)

    async def _execute_api(
        self, user_requirement: str, output_pathname: str, legacy_prd_filename: str, extra_info: str
    ) -> str:
        content = "#### User Requirements\n{user_requirement}\n#### Extra Info\n{extra_info}\n".format(
            user_requirement=to_markdown_code_block(val=user_requirement),
            extra_info=to_markdown_code_block(val=extra_info),
        )
        async with DocsReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "prd"}, "meta")
            req = Document(content=content)
            if not legacy_prd_filename:
                node = await self._new_prd(requirement=req.content)
                new_prd = Document(content=node.instruct_content.model_dump_json())
            else:
                content = await aread(filename=legacy_prd_filename)
                old_prd = Document(content=content)
                new_prd = await self._merge(req=req, related_doc=old_prd)

            if not output_pathname:
                output_pathname = self.config.workspace.path / "docs" / "prd.json"
            elif not Path(output_pathname).is_absolute():
                output_pathname = self.config.workspace.path / output_pathname
            output_pathname = rectify_pathname(path=output_pathname, default_filename="prd.json")
            await awrite(filename=output_pathname, data=new_prd.content)
            competitive_analysis_filename = output_pathname.parent / f"{output_pathname.stem}-competitive-analysis"
            await self._save_competitive_analysis(prd_doc=new_prd, output_filename=Path(competitive_analysis_filename))
            md_output_filename = output_pathname.with_suffix(".md")
            await save_json_to_markdown(content=new_prd.content, output_filename=md_output_filename)
            await reporter.async_report(md_output_filename, "path")
        return f'PRD filename: "{str(output_pathname)}". The  product requirement document (PRD) has been completed.'
