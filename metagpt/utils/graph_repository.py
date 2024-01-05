#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19
@Author  : mashenquan
@File    : graph_repository.py
@Desc    : Superclass for graph repository.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from pydantic import BaseModel

from metagpt.logs import logger
from metagpt.repo_parser import ClassInfo, ClassRelationship, RepoFileInfo
from metagpt.utils.common import concat_namespace


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
    CLASS_FUNCTION = "class_function"
    CLASS_PROPERTY = "class_property"
    HAS_CLASS_FUNCTION = "has_class_function"
    HAS_CLASS_PROPERTY = "has_class_property"
    HAS_CLASS = "has_class"
    HAS_PAGE_INFO = "has_page_info"
    HAS_CLASS_VIEW = "has_class_view"
    HAS_SEQUENCE_VIEW = "has_sequence_view"
    HAS_ARGS_DESC = "has_args_desc"
    HAS_TYPE_DESC = "has_type_desc"


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
    async def upsert(self, subject: str, predicate: str, object_: str):
        pass

    @abstractmethod
    async def update(self, subject: str, predicate: str, object_: str):
        pass

    @abstractmethod
    async def select(self, subject: str = None, predicate: str = None, object_: str = None) -> List[SPO]:
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
                    predicate=GraphKeyword.HAS_CLASS_FUNCTION,
                    object_=concat_namespace(file_info.file, class_name, fn),
                )
                await graph_db.insert(
                    subject=concat_namespace(file_info.file, class_name, fn),
                    predicate=GraphKeyword.IS,
                    object_=GraphKeyword.CLASS_FUNCTION,
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
    async def update_graph_db_with_class_views(graph_db: "GraphRepository", class_views: List[ClassInfo]):
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
                    subject=concat_namespace(c.package, vn), predicate=GraphKeyword.HAS_TYPE_DESC, object_=vt
                )
            for fn, desc in c.methods.items():
                if "</I>" in desc and "<I>" not in desc:
                    logger.error(desc)
                # class -> function
                await graph_db.insert(
                    subject=c.package,
                    predicate=GraphKeyword.HAS_CLASS_FUNCTION,
                    object_=concat_namespace(c.package, fn),
                )
                # function detail
                await graph_db.insert(
                    subject=concat_namespace(c.package, fn),
                    predicate=GraphKeyword.IS,
                    object_=GraphKeyword.CLASS_FUNCTION,
                )
                await graph_db.insert(
                    subject=concat_namespace(c.package, fn),
                    predicate=GraphKeyword.HAS_ARGS_DESC,
                    object_=desc,
                )

    @staticmethod
    async def update_graph_db_with_class_relationship_views(
        graph_db: "GraphRepository", relationship_views: List[ClassRelationship]
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
