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
from metagpt.config2 import config
from metagpt.const import (
    AGGREGATION,
    COMPOSITION,
    DATA_API_DESIGN_FILE_REPO,
    GENERALIZATION,
    GRAPH_REPO_FILE_REPO,
)
from metagpt.logs import logger
from metagpt.repo_parser import RepoParser
from metagpt.schema import ClassAttribute, ClassMethod, ClassView
from metagpt.utils.common import split_namespace
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.graph_repository import GraphKeyword, GraphRepository


class RebuildClassView(Action):
    async def run(self, with_messages=None, format=config.prompt_schema):
        graph_repo_pathname = self.context.git_repo.workdir / GRAPH_REPO_FILE_REPO / self.context.git_repo.workdir.name
        graph_db = await DiGraphRepository.load_from(str(graph_repo_pathname.with_suffix(".json")))
        repo_parser = RepoParser(base_directory=Path(self.i_context))
        # use pylint
        class_views, relationship_views, package_root = await repo_parser.rebuild_class_views(path=Path(self.i_context))
        await GraphRepository.update_graph_db_with_class_views(graph_db, class_views)
        await GraphRepository.update_graph_db_with_class_relationship_views(graph_db, relationship_views)
        # use ast
        direction, diff_path = self._diff_path(path_root=Path(self.i_context).resolve(), package_root=package_root)
        symbols = repo_parser.generate_symbols()
        for file_info in symbols:
            # Align to the same root directory in accordance with `class_views`.
            file_info.file = self._align_root(file_info.file, direction, diff_path)
            await GraphRepository.update_graph_db_with_file_info(graph_db, file_info)
        await self._create_mermaid_class_views(graph_db=graph_db)
        await graph_db.save()

    async def _create_mermaid_class_views(self, graph_db):
        path = Path(self.context.git_repo.workdir) / DATA_API_DESIGN_FILE_REPO
        path.mkdir(parents=True, exist_ok=True)
        pathname = path / self.context.git_repo.workdir.name
        async with aiofiles.open(str(pathname.with_suffix(".mmd")), mode="w", encoding="utf-8") as writer:
            content = "classDiagram\n"
            logger.debug(content)
            await writer.write(content)
            # class names
            rows = await graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)
            class_distinct = set()
            relationship_distinct = set()
            for r in rows:
                await RebuildClassView._create_mermaid_class(r.subject, graph_db, writer, class_distinct)
            for r in rows:
                await RebuildClassView._create_mermaid_relationship(r.subject, graph_db, writer, relationship_distinct)

    @staticmethod
    async def _create_mermaid_class(ns_class_name, graph_db, file_writer, distinct):
        fields = split_namespace(ns_class_name)
        if len(fields) > 2:
            # Ignore sub-class
            return

        class_view = ClassView(name=fields[1])
        rows = await graph_db.select(subject=ns_class_name)
        for r in rows:
            name = split_namespace(r.object_)[-1]
            name, visibility, abstraction = RebuildClassView._parse_name(name=name, language="python")
            if r.predicate == GraphKeyword.HAS_CLASS_PROPERTY:
                var_type = await RebuildClassView._parse_variable_type(r.object_, graph_db)
                attribute = ClassAttribute(
                    name=name, visibility=visibility, abstraction=bool(abstraction), value_type=var_type
                )
                class_view.attributes.append(attribute)
            elif r.predicate == GraphKeyword.HAS_CLASS_FUNCTION:
                method = ClassMethod(name=name, visibility=visibility, abstraction=bool(abstraction))
                await RebuildClassView._parse_function_args(method, r.object_, graph_db)
                class_view.methods.append(method)

        # update graph db
        await graph_db.insert(ns_class_name, GraphKeyword.HAS_CLASS_VIEW, class_view.model_dump_json())

        content = class_view.get_mermaid(align=1)
        logger.debug(content)
        await file_writer.write(content)
        distinct.add(ns_class_name)

    @staticmethod
    async def _create_mermaid_relationship(ns_class_name, graph_db, file_writer, distinct):
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
        for p, v in predicates.items():
            rows = await graph_db.select(subject=ns_class_name, predicate=p)
            for r in rows:
                o_fields = split_namespace(r.object_)
                if len(o_fields) > 2:
                    # Ignore sub-class
                    continue
                relationship = mappings.get(v, " .. ")
                link = f"{o_fields[1]}{relationship}{s_fields[1]}"
                distinct.add(link)
                content += f"\t{link}\n"

        if content:
            logger.debug(content)
            await file_writer.write(content)

    @staticmethod
    def _parse_name(name: str, language="python"):
        pattern = re.compile(r"<I>(.*?)<\/I>")
        result = re.search(pattern, name)

        abstraction = ""
        if result:
            name = result.group(1)
            abstraction = "*"
        if name.startswith("__"):
            visibility = "-"
        elif name.startswith("_"):
            visibility = "#"
        else:
            visibility = "+"
        return name, visibility, abstraction

    @staticmethod
    async def _parse_variable_type(ns_name, graph_db) -> str:
        rows = await graph_db.select(subject=ns_name, predicate=GraphKeyword.HAS_TYPE_DESC)
        if not rows:
            return ""
        vals = rows[0].object_.replace("'", "").split(":")
        if len(vals) == 1:
            return ""
        val = vals[-1].strip()
        return "" if val == "NoneType" else val + " "

    @staticmethod
    async def _parse_function_args(method: ClassMethod, ns_name: str, graph_db: GraphRepository):
        rows = await graph_db.select(subject=ns_name, predicate=GraphKeyword.HAS_ARGS_DESC)
        if not rows:
            return
        info = rows[0].object_.replace("'", "")

        fs_tag = "("
        ix = info.find(fs_tag)
        fe_tag = "):"
        eix = info.rfind(fe_tag)
        if eix < 0:
            fe_tag = ")"
            eix = info.rfind(fe_tag)
        args_info = info[ix + len(fs_tag) : eix].strip()
        method.return_type = info[eix + len(fe_tag) :].strip()
        if method.return_type == "None":
            method.return_type = ""
        if "(" in method.return_type:
            method.return_type = method.return_type.replace("(", "Tuple[").replace(")", "]")

        # parse args
        if not args_info:
            return
        splitter_ixs = []
        cost = 0
        for i in range(len(args_info)):
            if args_info[i] == "[":
                cost += 1
            elif args_info[i] == "]":
                cost -= 1
            if args_info[i] == "," and cost == 0:
                splitter_ixs.append(i)
        splitter_ixs.append(len(args_info))
        args = []
        ix = 0
        for eix in splitter_ixs:
            args.append(args_info[ix:eix])
            ix = eix + 1
        for arg in args:
            parts = arg.strip().split(":")
            if len(parts) == 1:
                method.args.append(ClassAttribute(name=parts[0].strip()))
                continue
            method.args.append(ClassAttribute(name=parts[0].strip(), value_type=parts[-1].strip()))

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
