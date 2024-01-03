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

from metagpt.actions import Action
from metagpt.config import CONFIG
from metagpt.const import CLASS_VIEW_FILE_REPO, GRAPH_REPO_FILE_REPO
from metagpt.repo_parser import RepoParser
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.graph_repository import GraphKeyword, GraphRepository


class RebuildClassView(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name=name, context=context, llm=llm)

    async def run(self, with_messages=None, format=CONFIG.prompt_schema):
        graph_repo_pathname = CONFIG.git_repo.workdir / GRAPH_REPO_FILE_REPO / CONFIG.git_repo.workdir.name
        graph_db = await DiGraphRepository.load_from(str(graph_repo_pathname.with_suffix(".json")))
        repo_parser = RepoParser(base_directory=self.context)
        class_views = await repo_parser.rebuild_class_views(path=Path(self.context))  # use pylint
        await GraphRepository.update_graph_db_with_class_views(graph_db, class_views)
        symbols = repo_parser.generate_symbols()  # use ast
        for file_info in symbols:
            await GraphRepository.update_graph_db_with_file_info(graph_db, file_info)
        await self._create_mermaid_class_view(graph_db=graph_db)
        await self._save(graph_db=graph_db)

    async def _create_mermaid_class_view(self, graph_db):
        pass
        # dataset = await graph_db.select(subject=concat_namespace(filename, class_name), predicate=GraphKeyword.HAS_PAGE_INFO)
        # if not dataset:
        #     logger.warning(f"No page info for {concat_namespace(filename, class_name)}")
        #     return
        # code_block_info = CodeBlockInfo.parse_raw(dataset[0].object_)
        # src_code = await read_file_block(filename=Path(self.context) / filename, lineno=code_block_info.lineno, end_lineno=code_block_info.end_lineno)
        # code_type = ""
        # dataset = await graph_db.select(subject=filename, predicate=GraphKeyword.IS)
        # for spo in dataset:
        #     if spo.object_ in ["javascript", "python"]:
        #         code_type = spo.object_
        #         break

        # try:
        #     node = await REBUILD_CLASS_VIEW_NODE.fill(context=f"```{code_type}\n{src_code}\n```", llm=self.llm, to=format)
        #     class_view = node.instruct_content.model_dump()["Class View"]
        # except Exception as e:
        #     class_view = RepoParser.rebuild_class_view(src_code, code_type)
        # await graph_db.insert(subject=concat_namespace(filename, class_name), predicate=GraphKeyword.HAS_CLASS_VIEW, object_=class_view)
        # logger.info(f"{concat_namespace(filename, class_name)} {GraphKeyword.HAS_CLASS_VIEW} {class_view}")

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
