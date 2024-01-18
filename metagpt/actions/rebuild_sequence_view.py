#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4
@Author  : mashenquan
@File    : rebuild_sequence_view.py
@Desc    : Rebuild sequence view info
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions import Action
from metagpt.config2 import config
from metagpt.const import GRAPH_REPO_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import ClassView
from metagpt.utils.common import aread, general_after_log, list_files, split_namespace
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.graph_repository import SPO, GraphKeyword, GraphRepository


class RebuildSequenceView(Action):
    graph_db: Optional[GraphRepository] = None

    async def run(self, with_messages=None, format=config.prompt_schema):
        graph_repo_pathname = self.context.git_repo.workdir / GRAPH_REPO_FILE_REPO / self.context.git_repo.workdir.name
        self.graph_db = await DiGraphRepository.load_from(str(graph_repo_pathname.with_suffix(".json")))
        entries = await self._search_main_entry()
        for entry in entries:
            await self._rebuild_sequence_view(entry)
        await self.graph_db.save()

    async def _search_main_entry(self) -> List:
        rows = await self.graph_db.select(predicate=GraphKeyword.HAS_PAGE_INFO)
        tag = "__name__:__main__"
        entries = []
        for r in rows:
            if tag in r.subject or tag in r.object_:
                entries.append(r)
        return entries

    async def _rebuild_sequence_view(self, entry):
        filename = entry.subject.split(":", 1)[0]
        src_filename = RebuildSequenceView._get_full_filename(root=self.i_context, pathname=filename)
        if not src_filename:
            return
        content = await aread(filename=src_filename, encoding="utf-8")
        content = f"```python\n{content}\n```\n\n---\nTranslate the code above into Mermaid Sequence Diagram."
        sequence_view = await self.llm.aask(
            msg=content, system_msgs=["You are a python code to Mermaid Sequence Diagram translator in function detail"]
        )
        await self.graph_db.insert(subject=filename, predicate=GraphKeyword.HAS_SEQUENCE_VIEW, object_=sequence_view)
        logger.info(sequence_view)

        merged_class_views = set()
        while True:
            participants = RebuildSequenceView.parse_participant(sequence_view)
            class_views = await self._get_class_views(participants)
            diff = set()
            for cv in class_views:
                if cv.subject in merged_class_views:
                    continue
                class_functionality, class_view = await self._parse_class_functionality(cv)
                sequence_view = await self._merge_sequence_view(sequence_view, class_view, class_functionality)
                diff.add(cv.subject)
                merged_class_views.add(cv.subject)

                await self.graph_db.delete(subject=filename, predicate=GraphKeyword.HAS_SEQUENCE_VIEW)
                await self.graph_db.insert(
                    subject=filename, predicate=GraphKeyword.HAS_SEQUENCE_VIEW, object_=sequence_view
                )
                logger.info(sequence_view)
            if diff:
                continue
            break

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _parse_class_functionality(self, spo):
        class_view = ClassView.model_validate_json(spo.object_)
        class_view_content = f"```mermaid\n{class_view.get_mermaid(align=0)}\n```"
        rsp = await self.llm.aask(
            msg=f"## Class View\n{class_view_content}",
            system_msgs=[
                "You are a tool capable of translating class views into a textual description of their functionalities and goals.",
                'Please return a Markdown JSON format with a "description" key containing a concise textual description of the class functionalities, a "goal" key containing a concise textual description of the problem the class aims to solve, and a "reason" key explaining why.',
            ],
        )

        class _JsonCodeBlock(BaseModel):
            description: str
            goal: str
            reason: Optional[str] = None

        code_block = rsp.removeprefix("```json\n").removesuffix("```")
        data = _JsonCodeBlock.model_validate_json(code_block)
        data.reason = None
        functionality = data.model_dump_json(exclude_none=True)
        await self.graph_db.insert(subject=spo.subject, predicate=GraphKeyword.HAS_CLASS_DESC, object_=functionality)
        return functionality, class_view_content

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _merge_sequence_view(self, sequence_view, class_view, class_functionality) -> str:
        contents = [
            f"## Mermaid Class View\n{class_view}",
            f"## Class Description\n{class_functionality}",
            f"## Mermaid Sequence View\n{sequence_view}",
        ]
        msg = "\n---\n".join(contents)
        rsp = await self.llm.aask(
            msg=msg,
            system_msgs=[
                "You are a tool to merge Mermaid class view information into the Mermaid sequence view.",
                'Append as much information as possible from the "Mermaid Class View" and "Class Description" to the sequence diagram.',
                'Return a markdown JSON format with a "sequence_diagram" key containing the merged Mermaid sequence view, a "reason" key explaining what information have been merged and why.',
            ],
        )

        class _JsonCodeBlock(BaseModel):
            sequence_diagram: str
            reason: str

        code_block = rsp.removeprefix("```json\n").removesuffix("```")
        data = _JsonCodeBlock.model_validate_json(code_block)
        return data.sequence_diagram

    @staticmethod
    def _get_full_filename(root: str | Path, pathname: str | Path) -> Path | None:
        files = list_files(root=root)
        postfix = "/" + str(pathname)
        for i in files:
            if str(i).endswith(postfix):
                return i
        return None

    @staticmethod
    def parse_participant(mermaid_sequence_diagram: str) -> List[str]:
        pattern = r"participant (\w+)"
        matches = re.findall(pattern, mermaid_sequence_diagram)
        return matches

    async def _get_class_views(self, class_names) -> List[SPO]:
        rows = await self.graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)

        ns_class_names = {}
        for r in rows:
            ns, class_name = split_namespace(r.subject)
            if class_name in class_names:
                ns_class_names[r.subject] = class_name

        class_views = []
        for ns_name in ns_class_names.keys():
            views = await self.graph_db.select(subject=ns_name, predicate=GraphKeyword.HAS_CLASS_VIEW)
            if not views:
                continue
            class_views += views
        return class_views
