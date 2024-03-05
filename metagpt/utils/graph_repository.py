#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19
@Author  : mashenquan
@File    : graph_repository.py
@Desc    : Superclass for graph repository. This script defines a superclass for a graph repository, providing a
    foundation for specific implementations.

"""

from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import List

from pydantic import BaseModel

from metagpt.repo_parser import DotClassInfo, DotClassRelationship, RepoFileInfo
from metagpt.utils.common import concat_namespace, split_namespace


class GraphKeyword:
    """Basic words for a Graph database.

    This class defines a set of basic words commonly used in the context of a Graph database.
    """

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
    HAS_SEQUENCE_VIEW_VER = "has_sequence_view_ver"
    HAS_CLASS_USE_CASE = "has_class_use_case"
    IS_COMPOSITE_OF = "is_composite_of"
    IS_AGGREGATE_OF = "is_aggregate_of"
    HAS_PARTICIPANT = "has_participant"


class SPO(BaseModel):
    """Graph repository record type.

    This class represents a record in a graph repository with three components:
    - Subject: The subject of the triple.
    - Predicate: The predicate describing the relationship between the subject and the object.
    - Object: The object of the triple.

    Attributes:
        subject (str): The subject of the triple.
        predicate (str): The predicate describing the relationship.
        object_ (str): The object of the triple.

    Example:
        spo_record = SPO(subject="Node1", predicate="connects_to", object_="Node2")
        # Represents a triple: Node1 connects_to Node2
    """

    subject: str
    predicate: str
    object_: str


class GraphRepository(ABC):
    """Abstract base class for a Graph Repository.

    This class defines the interface for a graph repository, providing methods for inserting, selecting,
    deleting, and saving graph data. Concrete implementations of this class must provide functionality
    for these operations.
    """

    def __init__(self, name: str, **kwargs):
        self._repo_name = name
        self._kwargs = kwargs

    @abstractmethod
    async def insert(self, subject: str, predicate: str, object_: str):
        """Insert a new triple into the graph repository.

        Args:
            subject (str): The subject of the triple.
            predicate (str): The predicate describing the relationship.
            object_ (str): The object of the triple.

        Example:
            await my_repository.insert(subject="Node1", predicate="connects_to", object_="Node2")
            # Inserts a triple: Node1 connects_to Node2 into the graph repository.
        """
        pass

    @abstractmethod
    async def select(self, subject: str = None, predicate: str = None, object_: str = None) -> List[SPO]:
        """Retrieve triples from the graph repository based on specified criteria.

        Args:
            subject (str, optional): The subject of the triple to filter by.
            predicate (str, optional): The predicate describing the relationship to filter by.
            object_ (str, optional): The object of the triple to filter by.

        Returns:
            List[SPO]: A list of SPO objects representing the selected triples.

        Example:
            selected_triples = await my_repository.select(subject="Node1", predicate="connects_to")
            # Retrieves triples where Node1 is the subject and the predicate is 'connects_to'.
        """
        pass

    @abstractmethod
    async def delete(self, subject: str = None, predicate: str = None, object_: str = None) -> int:
        """Delete triples from the graph repository based on specified criteria.

        Args:
            subject (str, optional): The subject of the triple to filter by.
            predicate (str, optional): The predicate describing the relationship to filter by.
            object_ (str, optional): The object of the triple to filter by.

        Returns:
            int: The number of triples deleted from the repository.

        Example:
            deleted_count = await my_repository.delete(subject="Node1", predicate="connects_to")
            # Deletes triples where Node1 is the subject and the predicate is 'connects_to'.
        """
        pass

    @abstractmethod
    async def save(self):
        """Save any changes made to the graph repository.

        Example:
            await my_repository.save()
            # Persists any changes made to the graph repository.
        """
        pass

    @property
    def name(self) -> str:
        """Get the name of the graph repository."""
        return self._repo_name

    @staticmethod
    async def update_graph_db_with_file_info(graph_db: "GraphRepository", file_info: RepoFileInfo):
        """Insert information of RepoFileInfo into the specified graph repository.

        This function updates the provided graph repository with information from the given RepoFileInfo object.
        The function inserts triples related to various dimensions such as file type, class, class method, function,
        global variable, and page info.

        Triple Patterns:
        - (?, is, [file type])
        - (?, has class, ?)
        - (?, is, [class])
        - (?, has class method, ?)
        - (?, has function, ?)
        - (?, is, [function])
        - (?, is, global variable)
        - (?, has page info, ?)

        Args:
            graph_db (GraphRepository): The graph repository object to be updated.
            file_info (RepoFileInfo): The RepoFileInfo object containing information to be inserted.

        Example:
            await update_graph_db_with_file_info(my_graph_repo, my_file_info)
            # Updates 'my_graph_repo' with information from 'my_file_info'.
        """
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
        """Insert dot format class information into the specified graph repository.

        This function updates the provided graph repository with class information from the given list of DotClassInfo objects.
        The function inserts triples related to various aspects of class views, including source code, file type, class,
        class property, class detail, method, composition, and aggregation.

        Triple Patterns:
        - (?, is, source code)
        - (?, is, file type)
        - (?, has class, ?)
        - (?, is, class)
        - (?, has class property, ?)
        - (?, is, class property)
        - (?, has detail, ?)
        - (?, has method, ?)
        - (?, is composite of, ?)
        - (?, is aggregate of, ?)

        Args:
            graph_db (GraphRepository): The graph repository object to be updated.
            class_views (List[DotClassInfo]): List of DotClassInfo objects containing class information to be inserted.


        Example:
            await update_graph_db_with_class_views(my_graph_repo, [class_info1, class_info2])
            # Updates 'my_graph_repo' with class information from the provided list of DotClassInfo objects.
        """
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
        """Insert class relationships and labels into the specified graph repository.

        This function updates the provided graph repository with class relationship information from the given list
        of DotClassRelationship objects. The function inserts triples representing relationships and labels between
        classes.

        Triple Patterns:
        - (?, is relationship of, ?)
        - (?, is relationship on, ?)

        Args:
            graph_db (GraphRepository): The graph repository object to be updated.
            relationship_views (List[DotClassRelationship]): List of DotClassRelationship objects containing
            class relationship information to be inserted.

        Example:
            await update_graph_db_with_class_relationship_views(my_graph_repo, [relationship1, relationship2])
            # Updates 'my_graph_repo' with class relationship information from the provided list of DotClassRelationship objects.

        """
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
        """Append namespace-prefixed information to relationship SPO (Subject-Predicate-Object) objects in the graph
            repository.

        This function updates the provided graph repository by appending namespace-prefixed information to existing
        relationship SPO objects.

        Args:
            graph_db (GraphRepository): The graph repository object to be updated.
        """
        classes = await graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)
        mapping = defaultdict(list)
        for c in classes:
            name = split_namespace(c.subject)[-1]
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
