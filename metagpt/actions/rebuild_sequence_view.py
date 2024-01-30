#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4
@Author  : mashenquan
@File    : rebuild_sequence_view.py
@Desc    : Rebuild sequence view info
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from metagpt.actions import Action
from metagpt.config2 import config
from metagpt.const import GRAPH_REPO_FILE_REPO
from metagpt.logs import logger
from metagpt.utils.common import aread, list_files
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.graph_repository import GraphKeyword


class RebuildSequenceView(Action):
    async def run(self, with_messages=None, format=config.prompt_schema):
        graph_repo_pathname = self.context.git_repo.workdir / GRAPH_REPO_FILE_REPO / self.context.git_repo.workdir.name
        graph_db = await DiGraphRepository.load_from(str(graph_repo_pathname.with_suffix(".json")))
        entries = await RebuildSequenceView._search_main_entry(graph_db)
        for entry in entries:
            await self._rebuild_sequence_view(entry, graph_db)
        await graph_db.save()

    @staticmethod
    async def _search_main_entry(graph_db) -> List:
        rows = await graph_db.select(predicate=GraphKeyword.HAS_PAGE_INFO)
        tag = "__name__:__main__"
        entries = []
        for r in rows:
            if tag in r.subject or tag in r.object_:
                entries.append(r)
        return entries

    async def _rebuild_sequence_view(self, entry, graph_db):
        filename = entry.subject.split(":", 1)[0]
        src_filename = RebuildSequenceView._get_full_filename(root=self.i_context, pathname=filename)
        if not src_filename:
            return
        content = await aread(filename=src_filename, encoding="utf-8")
        content = f"```python\n{content}\n```\n\n---\nTranslate the code above into Mermaid Sequence Diagram."
        data = await self.llm.aask(
            msg=content, system_msgs=["You are a python code to Mermaid Sequence Diagram translator in function detail"]
        )
        await graph_db.insert(subject=filename, predicate=GraphKeyword.HAS_SEQUENCE_VIEW, object_=data)
        logger.info(data)

    @staticmethod
    def _get_full_filename(root: str | Path, pathname: str | Path) -> Path | None:
        files = list_files(root=root)
        postfix = "/" + str(pathname)
        for i in files:
            if str(i).endswith(postfix):
                return i
        return None
