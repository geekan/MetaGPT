#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19
@Author  : mashenquan
@File    : graph_repository.py
@Desc    : Superclass for graph repository.
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import List

from pydantic import BaseModel

from metagpt.repo_parser import DotClassInfo, DotClassRelationship, RepoFileInfo
from metagpt.utils.common import concat_namespace, split_namespace


class GraphKeyword:
    IS = "is"
    OF = "Of"
    ON = "On"
    CLASS = "class"
    FUNCTION = "function"
    HAS_FUNCTION = "has_function"
    SOURCE_CODE = "source_code"
    NULL = "<null>"
    GLOBAL_VARIABLE = "global_variable"
    CLASS_METHOD = "class_method"
    CLASS_PROPERTY = "class_property"
    HAS_CLASS_METHOD = "has_class_method"
    HAS_CLASS_PROPERTY = "has_class_property"
    HAS_CLASS = "has_class"
    HAS_DETAIL = "has_detail"
    HAS_PAGE_INFO = "has_page_info"
    HAS_CLASS_VIEW = "has_class_view"
    HAS_SEQUENCE_VIEW = "has_sequence_view"
    IS_COMPOSITE_OF = "is_composite_of"
    IS_AGGREGATE_OF = "is_aggregate_of"


class SPO(BaseModel):
    subject: str
    predicate: str
    object_: str


class GraphRepository(ABC):
    def __init__(self, name: str, **kwargs):
        self._repo_name = name
        self._kwargs = kwargs

    @abstractmethod
    async def insert(self, subject: str, predicate: str, object_: str):
        pass

    @abstractmethod
    async def select(self, subject: str = None, predicate: str = None, object_: str = None) -> List[SPO]:
        pass

    @abstractmethod
    async def delete(self, subject: str = None, predicate: str = None, object_: str = None) -> int:
        pass

    @abstractmethod
    async def save(self):
        pass

    @property
    def name(self) -> str:
        return self._repo_name

    @staticmethod
    async def update_graph_db_with_file_info(graph_db: "GraphRepository", file_info: RepoFileInfo):
        await graph_db.insert(subject=file_info.file, predicate=GraphKeyword.IS, object_=GraphKeyword.SOURCE_CODE)
        file_types = {".py": "python", ".js": "javascript"}
        file_type = file_types.get(Path(file_info.file).suffix, GraphKeyword.NULL)
        await graph_db.insert(subject=file_info.file, predicate=GraphKeyword.IS, object_=file_type)
        for c in file_info.classes:
            class_name = c.get("name", "")
            # file -> class
            await graph_db.insert(
                subject=file_info.file,
                predicate=GraphKeyword.HAS_CLASS,
                object_=concat_namespace(file_info.file, class_name),
            )
            # class detail
            await graph_db.insert(
                subject=concat_namespace(file_info.file, class_name),
                predicate=GraphKeyword.IS,
                object_=GraphKeyword.CLASS,
            )
            methods = c.get("methods", [])
            for fn in methods:
                await graph_db.insert(
                    subject=concat_namespace(file_info.file, class_name),
                    predicate=GraphKeyword.HAS_CLASS_METHOD,
                    object_=concat_namespace(file_info.file, class_name, fn),
                )
                await graph_db.insert(
                    subject=concat_namespace(file_info.file, class_name, fn),
                    predicate=GraphKeyword.IS,
                    object_=GraphKeyword.CLASS_METHOD,
                )
        for f in file_info.functions:
            # file -> function
            await graph_db.insert(
                subject=file_info.file, predicate=GraphKeyword.HAS_FUNCTION, object_=concat_namespace(file_info.file, f)
            )
            # function detail
            await graph_db.insert(
                subject=concat_namespace(file_info.file, f), predicate=GraphKeyword.IS, object_=GraphKeyword.FUNCTION
            )
        for g in file_info.globals:
            await graph_db.insert(
                subject=concat_namespace(file_info.file, g),
                predicate=GraphKeyword.IS,
                object_=GraphKeyword.GLOBAL_VARIABLE,
            )
        for code_block in file_info.page_info:
            if code_block.tokens:
                await graph_db.insert(
                    subject=concat_namespace(file_info.file, *code_block.tokens),
                    predicate=GraphKeyword.HAS_PAGE_INFO,
                    object_=code_block.model_dump_json(),
                )
            for k, v in code_block.properties.items():
                await graph_db.insert(
                    subject=concat_namespace(file_info.file, k, v),
                    predicate=GraphKeyword.HAS_PAGE_INFO,
                    object_=code_block.model_dump_json(),
                )

    @staticmethod
    async def update_graph_db_with_class_views(graph_db: "GraphRepository", class_views: List[DotClassInfo]):
        for c in class_views:
            filename, _ = c.package.split(":", 1)
            await graph_db.insert(subject=filename, predicate=GraphKeyword.IS, object_=GraphKeyword.SOURCE_CODE)
            file_types = {".py": "python", ".js": "javascript"}
            file_type = file_types.get(Path(filename).suffix, GraphKeyword.NULL)
            await graph_db.insert(subject=filename, predicate=GraphKeyword.IS, object_=file_type)
            await graph_db.insert(subject=filename, predicate=GraphKeyword.HAS_CLASS, object_=c.package)
            await graph_db.insert(
                subject=c.package,
                predicate=GraphKeyword.IS,
                object_=GraphKeyword.CLASS,
            )
            await graph_db.insert(subject=c.package, predicate=GraphKeyword.HAS_DETAIL, object_=c.model_dump_json())
            for vn, vt in c.attributes.items():
                # class -> property
                await graph_db.insert(
                    subject=c.package,
                    predicate=GraphKeyword.HAS_CLASS_PROPERTY,
                    object_=concat_namespace(c.package, vn),
                )
                # property detail
                await graph_db.insert(
                    subject=concat_namespace(c.package, vn),
                    predicate=GraphKeyword.IS,
                    object_=GraphKeyword.CLASS_PROPERTY,
                )
                await graph_db.insert(
                    subject=concat_namespace(c.package, vn),
                    predicate=GraphKeyword.HAS_DETAIL,
                    object_=vt.model_dump_json(),
                )
            for fn, ft in c.methods.items():
                # class -> function
                await graph_db.insert(
                    subject=c.package,
                    predicate=GraphKeyword.HAS_CLASS_METHOD,
                    object_=concat_namespace(c.package, fn),
                )
                # function detail
                await graph_db.insert(
                    subject=concat_namespace(c.package, fn),
                    predicate=GraphKeyword.IS,
                    object_=GraphKeyword.CLASS_METHOD,
                )
                await graph_db.insert(
                    subject=concat_namespace(c.package, fn),
                    predicate=GraphKeyword.HAS_DETAIL,
                    object_=ft.model_dump_json(),
                )
            for i in c.compositions:
                await graph_db.insert(
                    subject=c.package, predicate=GraphKeyword.IS_COMPOSITE_OF, object_=concat_namespace("?", i)
                )
            for i in c.aggregations:
                await graph_db.insert(
                    subject=c.package, predicate=GraphKeyword.IS_AGGREGATE_OF, object_=concat_namespace("?", i)
                )

    @staticmethod
    async def update_graph_db_with_class_relationship_views(
        graph_db: "GraphRepository", relationship_views: List[DotClassRelationship]
    ):
        for r in relationship_views:
            await graph_db.insert(
                subject=r.src, predicate=GraphKeyword.IS + r.relationship + GraphKeyword.OF, object_=r.dest
            )
            if not r.label:
                continue
            await graph_db.insert(
                subject=r.src,
                predicate=GraphKeyword.IS + r.relationship + GraphKeyword.ON,
                object_=concat_namespace(r.dest, r.label),
            )

    @staticmethod
    async def rebuild_composition_relationship(graph_db: "GraphRepository"):
        classes = await graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)
        mapping = defaultdict(list)
        for c in classes:
            _, name = split_namespace(c.subject)
            mapping[name].append(c.subject)

        rows = await graph_db.select(predicate=GraphKeyword.IS_COMPOSITE_OF)
        for r in rows:
            ns, class_ = split_namespace(r.object_)
            if ns != "?":
                continue
            val = mapping[class_]
            if len(val) != 1:
                continue
            ns_name = val[0]
            await graph_db.delete(subject=r.subject, predicate=r.predicate, object_=r.object_)
            await graph_db.insert(subject=r.subject, predicate=r.predicate, object_=ns_name)
