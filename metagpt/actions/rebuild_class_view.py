#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19
@Author  : mashenquan
@File    : rebuild_class_view.py
@Desc    : Rebuild class view info
"""

from pathlib import Path
from typing import Optional

import aiofiles

from metagpt.actions import Action
from metagpt.config2 import config
from metagpt.const import (
    AGGREGATION,
    COMPOSITION,
    DATA_API_DESIGN_FILE_REPO,
    GENERALIZATION,
    GRAPH_REPO_FILE_REPO,
)
from metagpt.logs import logger
from metagpt.repo_parser import DotClassInfo, RepoParser
from metagpt.schema import UMLClassAttribute, UMLClassMethod, UMLClassView
from metagpt.utils.common import concat_namespace, split_namespace
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.graph_repository import GraphKeyword, GraphRepository


class RebuildClassView(Action):
    graph_db: Optional[GraphRepository] = None

    async def run(self, with_messages=None, format=config.prompt_schema):
        graph_repo_pathname = self.context.git_repo.workdir / GRAPH_REPO_FILE_REPO / self.context.git_repo.workdir.name
        self.graph_db = await DiGraphRepository.load_from(str(graph_repo_pathname.with_suffix(".json")))
        repo_parser = RepoParser(base_directory=Path(self.i_context))
        # use pylint
        class_views, relationship_views, package_root = await repo_parser.rebuild_class_views(path=Path(self.i_context))
        await GraphRepository.update_graph_db_with_class_views(self.graph_db, class_views)
        await GraphRepository.update_graph_db_with_class_relationship_views(self.graph_db, relationship_views)
        await GraphRepository.rebuild_composition_relationship(self.graph_db)
        # use ast
        direction, diff_path = self._diff_path(path_root=Path(self.i_context).resolve(), package_root=package_root)
        symbols = repo_parser.generate_symbols()
        for file_info in symbols:
            # Align to the same root directory in accordance with `class_views`.
            file_info.file = self._align_root(file_info.file, direction, diff_path)
            await GraphRepository.update_graph_db_with_file_info(self.graph_db, file_info)
        await self._create_mermaid_class_views()
        await self.graph_db.save()

    async def _create_mermaid_class_views(self):
        path = Path(self.context.git_repo.workdir) / DATA_API_DESIGN_FILE_REPO
        path.mkdir(parents=True, exist_ok=True)
        pathname = path / self.context.git_repo.workdir.name
        async with aiofiles.open(str(pathname.with_suffix(".mmd")), mode="w", encoding="utf-8") as writer:
            content = "classDiagram\n"
            logger.debug(content)
            await writer.write(content)
            # class names
            rows = await self.graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)
            class_distinct = set()
            relationship_distinct = set()
            for r in rows:
                content = await self._create_mermaid_class(r.subject)
                if content:
                    await writer.write(content)
                    class_distinct.add(r.subject)
            for r in rows:
                content, distinct = await self._create_mermaid_relationship(r.subject)
                if content:
                    logger.debug(content)
                    await writer.write(content)
                    relationship_distinct.update(distinct)
        logger.info(f"classes: {len(class_distinct)}, relationship: {len(relationship_distinct)}")

    async def _create_mermaid_class(self, ns_class_name) -> str:
        fields = split_namespace(ns_class_name)
        if len(fields) > 2:
            # Ignore sub-class
            return ""

        rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_DETAIL)
        if not rows:
            return ""
        dot_class_info = DotClassInfo.model_validate_json(rows[0].object_)
        visibility = UMLClassView.name_to_visibility(dot_class_info.name)
        class_view = UMLClassView(name=dot_class_info.name, visibility=visibility)
        for i in dot_class_info.attributes.values():
            visibility = UMLClassAttribute.name_to_visibility(i.name)
            attr = UMLClassAttribute(name=i.name, visibility=visibility, value_type=i.type_, default_value=i.default_)
            class_view.attributes.append(attr)
        for i in dot_class_info.methods.values():
            visibility = UMLClassMethod.name_to_visibility(i.name)
            method = UMLClassMethod(name=i.name, visibility=visibility, return_type=i.return_args.type_)
            for j in i.args:
                arg = UMLClassAttribute(name=j.name, value_type=j.type_, default_value=j.default_)
                method.args.append(arg)

        # update uml view
        await self.graph_db.insert(ns_class_name, GraphKeyword.HAS_CLASS_VIEW, class_view.model_dump_json())
        # update uml isCompositeOf
        for c in dot_class_info.compositions:
            await self.graph_db.insert(
                subject=ns_class_name,
                predicate=GraphKeyword.IS + COMPOSITION + GraphKeyword.OF,
                object_=concat_namespace("?", c),
            )

        # update uml isAggregateOf
        for a in dot_class_info.aggregations:
            await self.graph_db.insert(
                subject=ns_class_name,
                predicate=GraphKeyword.IS + AGGREGATION + GraphKeyword.OF,
                object_=concat_namespace("?", a),
            )

        content = class_view.get_mermaid(align=1)
        logger.debug(content)
        return content

    async def _create_mermaid_relationship(self, ns_class_name):
        s_fields = split_namespace(ns_class_name)
        if len(s_fields) > 2:
            # Ignore sub-class
            return

        predicates = {GraphKeyword.IS + v + GraphKeyword.OF: v for v in [GENERALIZATION, COMPOSITION, AGGREGATION]}
        mappings = {
            GENERALIZATION: " <|-- ",
            COMPOSITION: " *-- ",
            AGGREGATION: " o-- ",
        }
        content = ""
        distinct = set()
        for p, v in predicates.items():
            rows = await self.graph_db.select(subject=ns_class_name, predicate=p)
            for r in rows:
                o_fields = split_namespace(r.object_)
                if len(o_fields) > 2:
                    # Ignore sub-class
                    continue
                relationship = mappings.get(v, " .. ")
                link = f"{o_fields[1]}{relationship}{s_fields[1]}"
                distinct.add(link)
                content += f"\t{link}\n"

        return content, distinct

    @staticmethod
    def _diff_path(path_root: Path, package_root: Path) -> (str, str):
        if len(str(path_root)) > len(str(package_root)):
            return "+", str(path_root.relative_to(package_root))
        if len(str(path_root)) < len(str(package_root)):
            return "-", str(package_root.relative_to(path_root))
        return "=", "."

    @staticmethod
    def _align_root(path: str, direction: str, diff_path: str):
        if direction == "=":
            return path
        if direction == "+":
            return diff_path + "/" + path
        else:
            return path[len(diff_path) + 1 :]
