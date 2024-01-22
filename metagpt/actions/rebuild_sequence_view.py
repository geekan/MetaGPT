#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4
@Author  : mashenquan
@File    : rebuild_sequence_view.py
@Desc    : Rebuild sequence view info
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions import Action
from metagpt.config2 import config
from metagpt.const import AGGREGATION, GENERALIZATION, GRAPH_REPO_FILE_REPO
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
            class_views, class_compositions = await self._get_class_views(participants)
            for compositions in class_compositions.values():
                for c in compositions:
                    ns, _ = split_namespace(c.object_)
                    if ns == "?":
                        continue
                    await self._parse_class_description(c.object_)
            diff = set()
            for cv in class_views:
                if cv.subject in merged_class_views:
                    continue
                await self._parse_class_description(cv.subject)
                sequence_view = await self._merge_sequence_view(
                    sequence_view, cv.subject, class_compositions.get(cv.subject, [])
                )
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
    async def _parse_class_description(self, ns_class_name: str):
        rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_DESC)
        if rows:
            return
        me_class_views = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_VIEW)
        if not me_class_views:
            # Loss of necessary information to create the description.
            await self.graph_db.insert(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_VIEW, object_="")
            return

        # prepare base-class description
        rows = await self.graph_db.select(
            subject=ns_class_name, predicate=GraphKeyword.IS + GENERALIZATION + GraphKeyword.OF
        )
        ns_base_class_names = [r.object_ for r in rows]
        ns_base_class_views = {}
        ns_base_class_descs = {}
        for name in ns_base_class_names:
            class_views = await self.graph_db.select(subject=name, predicate=GraphKeyword.HAS_CLASS_VIEW)
            if rows:
                ns_base_class_views[name] = class_views
            descs = await self.graph_db.select(subject=name, predicate=GraphKeyword.HAS_CLASS_DESC)
            if not descs:
                # Haven't been parsed before.
                await self._parse_class_description(ns_class_name=name)
                descs = await self.graph_db.select(subject=name, predicate=GraphKeyword.HAS_CLASS_DESC)
            ns_base_class_descs[name] = descs

        # parse class description
        prompt = "```mermaid\nclassDiagram\n"
        # - add base-class description
        for ns_name in ns_base_class_names:
            descs = ns_base_class_descs.get(ns_name, [])
            for r in descs:
                notes = self._desc_to_note(r.object_)
                ns, name = split_namespace(r.subject)
                for n in notes:
                    prompt += f'\n\tnote for {name} "{n}"'
            views = ns_base_class_views.get(ns_name, [])
            for r in views:
                cv = ClassView.model_validate_json(r.object_)
                prompt += "\n" + cv.get_mermaid(align=1)
        # - add relationship
        _, me = split_namespace(ns_class_name)
        for ns_name in ns_base_class_names:
            ns, base = split_namespace(ns_name)
            prompt += f"\n\t{base} <|-- {me}"
        # - add me
        cv = ClassView.model_validate_json(me_class_views[0].object_)
        prompt += "\n" + cv.get_mermaid(align=1)
        prompt += "\n```"

        rsp = await self.llm.aask(
            msg=prompt,
            system_msgs=[
                "You are a tool capable of translating class views into a textual description of their functionalities and goals.",
                f'Please return a Markdown JSON format with a "description" key containing a concise textual description of the `{me}` class functionalities, a "goal" key containing a concise textual description of the problem the `{me}` class aims to solve, and a "reason" key explaining why.',
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
        await self.graph_db.insert(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_DESC, object_=functionality)

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _merge_sequence_view(self, sequence_view, ns_class_name, compositions) -> str:
        class_view_part = "```mermaid\n"
        # add class
        class_view_part += await self._class_view_to_mermaid(ns_class_name)
        # add aggregation relationship
        _, me = split_namespace(ns_class_name)
        rows = await self.graph_db.select(
            subject=ns_class_name, predicate=GraphKeyword.IS + AGGREGATION + GraphKeyword.OF
        )
        aggregation = [r.object_ for r in rows]
        for ns_aggr_name in aggregation:
            _, name = split_namespace(ns_aggr_name)
            class_view_part += f"\n\t{me} *-- {name}"
            class_view_part += await self._class_view_to_mermaid(ns_aggr_name)
        # add composition relationship
        for c in compositions:
            _, name = split_namespace(c.object_)
            class_view_part += f"\n\t{me} *-- {name}"
            class_view_part += await self._class_view_to_mermaid(c.object_)

        class_view_part += "\n```"

        contents = [
            f"## Mermaid Class View\n{class_view_part}\n",
            f"## Mermaid Sequence View\n{sequence_view}",
        ]
        prompt = "\n---\n".join(contents)
        rsp = await self.llm.aask(
            msg=prompt,
            system_msgs=[
                "You are a tool to merge Mermaid class view information into the Mermaid sequence view.",
                'Append as much information as possible from the "Mermaid Class View" to the sequence diagram.',
                'Return a markdown JSON format with a "sequence_diagram" key containing the merged Mermaid sequence view, a "reason" key explaining in detail what information have been merged and why.',
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

    async def _get_class_views(self, class_names) -> (List[SPO], Dict[str, List[SPO]]):
        rows = await self.graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)

        ns_class_names = {}
        for r in rows:
            ns, class_name = split_namespace(r.subject)
            if class_name in class_names:
                ns_class_names[r.subject] = class_name

        class_views = []
        class_compositions = {}
        for ns_name in ns_class_names.keys():
            views = await self.graph_db.select(subject=ns_name, predicate=GraphKeyword.HAS_CLASS_VIEW)
            if not views:
                continue
            class_views += views
            compositions = await self.graph_db.select(subject=ns_name, predicate=GraphKeyword.IS_COMPOSITE_OF)
            class_compositions[ns_name] = compositions
        return class_views, class_compositions

    @staticmethod
    def _desc_to_note(json_str) -> List[str]:
        if not json_str:
            return []
        m = json.loads(json_str)
        return [s.replace('"', '\\"').replace("\n", "\\n") for s in m.values()]

    async def _class_view_to_mermaid(self, ns_class_name) -> str:
        class_view_rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_VIEW)
        if not class_view_rows:
            return ""
        result = ClassView.model_validate_json(class_view_rows[0].object_).get_mermaid() if class_view_rows else ""
        _, name = split_namespace(ns_class_name)
        class_desc_rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_DESC)
        if not class_desc_rows:
            # Haven't been parsed before.
            await self._parse_class_description(ns_class_name=ns_class_name)
            class_desc_rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_DESC)
        for r in self._desc_to_note(class_desc_rows[0].object_):
            result += f'\n\tnote for {name} "{r}"'
        return result
