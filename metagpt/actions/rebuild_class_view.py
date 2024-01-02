#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19
@Author  : mashenquan
@File    : rebuild_class_view.py
@Desc    : Rebuild class view info
"""
import re
from pathlib import Path

import aiofiles

from metagpt.actions import Action
from metagpt.config import CONFIG
from metagpt.const import (
    CLASS_VIEW_FILE_REPO,
    DATA_API_DESIGN_FILE_REPO,
    GRAPH_REPO_FILE_REPO,
)
from metagpt.repo_parser import RepoParser
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.graph_repository import GraphKeyword, GraphRepository


class RebuildClassView(Action):
    async def run(self, with_messages=None, format=CONFIG.prompt_schema):
        graph_repo_pathname = CONFIG.git_repo.workdir / GRAPH_REPO_FILE_REPO / CONFIG.git_repo.workdir.name
        graph_db = await DiGraphRepository.load_from(str(graph_repo_pathname.with_suffix(".json")))
        repo_parser = RepoParser(base_directory=Path(self.context))
        class_views, relationship_views = await repo_parser.rebuild_class_views(path=Path(self.context))  # use pylint
        await GraphRepository.update_graph_db_with_class_views(graph_db, class_views)
        await GraphRepository.update_graph_db_with_class_relationship_views(graph_db, relationship_views)
        symbols = repo_parser.generate_symbols()  # use ast
        for file_info in symbols:
            await GraphRepository.update_graph_db_with_file_info(graph_db, file_info)
        # await graph_db.save(path=graph_repo_pathname.parent)
        await self._create_mermaid_class_views(graph_db=graph_db)
        await self._save(graph_db=graph_db)

    async def _create_mermaid_class_views(self, graph_db):
        path = Path(CONFIG.git_repo.workdir) / DATA_API_DESIGN_FILE_REPO
        path.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(str(path / CONFIG.git_repo.workdir.name), mode="w", encoding="utf-8") as writer:
            await writer.write("classDiagram\n")
            # class names
            rows = await graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)
            distinct = {}
            for r in rows:
                await RebuildClassView._create_mermaid_class(r, graph_db, writer, distinct)

    @staticmethod
    async def _create_mermaid_class(ns_class_name, graph_db, file_writer, distinct):
        pass
        # fields = split_namespace(ns_class_name)
        # await graph_db.select(subject=ns_class_name)

    async def _save(self, graph_db):
        class_view_file_repo = CONFIG.git_repo.new_file_repository(relative_path=CLASS_VIEW_FILE_REPO)
        dataset = await graph_db.select(predicate=GraphKeyword.HAS_CLASS_VIEW)
        all_class_view = []
        for spo in dataset:
            title = f"---\ntitle: {spo.subject}\n---\n"
            filename = re.sub(r"[/:]", "_", spo.subject) + ".mmd"
            await class_view_file_repo.save(filename=filename, content=title + spo.object_)
            all_class_view.append(spo.object_)
        await class_view_file_repo.save(filename="all.mmd", content="\n".join(all_class_view))
