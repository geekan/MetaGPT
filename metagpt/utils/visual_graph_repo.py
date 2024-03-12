#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19
@Author  : mashenquan
@File    : visualize_graph.py
@Desc    : Visualization tool to visualize the class diagrams or sequence diagrams of the graph repository.
"""
from __future__ import annotations

import re
from abc import ABC
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from metagpt.const import AGGREGATION, COMPOSITION, GENERALIZATION
from metagpt.schema import UMLClassView
from metagpt.utils.common import split_namespace
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.graph_repository import GraphKeyword, GraphRepository


class _VisualClassView(BaseModel):
    """Protected class used by VisualGraphRepo internally.

    Attributes:
        package (str): The package associated with the class.
        uml (Optional[UMLClassView]): Optional UMLClassView associated with the class.
        generalizations (List[str]): List of generalizations for the class.
        compositions (List[str]): List of compositions for the class.
        aggregations (List[str]): List of aggregations for the class.
    """

    package: str
    uml: Optional[UMLClassView] = None
    generalizations: List[str] = Field(default_factory=list)
    compositions: List[str] = Field(default_factory=list)
    aggregations: List[str] = Field(default_factory=list)

    def get_mermaid(self, align: int = 1) -> str:
        """Creates a Markdown Mermaid class diagram text.

        Args:
            align (int): Indent count used for alignment.

        Returns:
            str: The Markdown text representing the Mermaid class diagram.
        """
        if not self.uml:
            return ""
        prefix = "\t" * align

        mermaid_txt = self.uml.get_mermaid(align=align)
        for i in self.generalizations:
            mermaid_txt += f"{prefix}{i} <|-- {self.name}\n"
        for i in self.compositions:
            mermaid_txt += f"{prefix}{i} *-- {self.name}\n"
        for i in self.aggregations:
            mermaid_txt += f"{prefix}{i} o-- {self.name}\n"
        return mermaid_txt

    @property
    def name(self) -> str:
        """Returns the class name without the namespace prefix."""
        return split_namespace(self.package)[-1]


class VisualGraphRepo(ABC):
    """Abstract base class for VisualGraphRepo."""

    graph_db: GraphRepository

    def __init__(self, graph_db):
        self.graph_db = graph_db


class VisualDiGraphRepo(VisualGraphRepo):
    """Implementation of VisualGraphRepo for DiGraph graph repository.

    This class extends VisualGraphRepo to provide specific functionality for a graph repository using DiGraph.
    """

    @classmethod
    async def load_from(cls, filename: str | Path):
        """Load a VisualDiGraphRepo instance from a file."""
        graph_db = await DiGraphRepository.load_from(str(filename))
        return cls(graph_db=graph_db)

    async def get_mermaid_class_view(self) -> str:
        """
        Returns a Markdown Mermaid class diagram code block object.
        """
        rows = await self.graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)
        mermaid_txt = "classDiagram\n"
        for r in rows:
            v = await self._get_class_view(ns_class_name=r.subject)
            mermaid_txt += v.get_mermaid()
        return mermaid_txt

    async def _get_class_view(self, ns_class_name: str) -> _VisualClassView:
        """Returns the Markdown Mermaid class diagram code block object for the specified class."""
        rows = await self.graph_db.select(subject=ns_class_name)
        class_view = _VisualClassView(package=ns_class_name)
        for r in rows:
            if r.predicate == GraphKeyword.HAS_CLASS_VIEW:
                class_view.uml = UMLClassView.model_validate_json(r.object_)
            elif r.predicate == GraphKeyword.IS + GENERALIZATION + GraphKeyword.OF:
                name = split_namespace(r.object_)[-1]
                name = self._refine_name(name)
                if name:
                    class_view.generalizations.append(name)
            elif r.predicate == GraphKeyword.IS + COMPOSITION + GraphKeyword.OF:
                name = split_namespace(r.object_)[-1]
                name = self._refine_name(name)
                if name:
                    class_view.compositions.append(name)
            elif r.predicate == GraphKeyword.IS + AGGREGATION + GraphKeyword.OF:
                name = split_namespace(r.object_)[-1]
                name = self._refine_name(name)
                if name:
                    class_view.aggregations.append(name)
        return class_view

    async def get_mermaid_sequence_views(self) -> List[(str, str)]:
        """Returns all Markdown sequence diagrams with their corresponding graph repository keys."""
        sequence_views = []
        rows = await self.graph_db.select(predicate=GraphKeyword.HAS_SEQUENCE_VIEW)
        for r in rows:
            sequence_views.append((r.subject, r.object_))
        return sequence_views

    @staticmethod
    def _refine_name(name: str) -> str:
        """Removes impurity content from the given name.

        Example:
            >>> _refine_name("int")
            ""

            >>> _refine_name('"Class1"')
            'Class1'

            >>> _refine_name("pkg.Class1")
            "Class1"
        """
        name = re.sub(r'^[\'"\\\(\)]+|[\'"\\\(\)]+$', "", name)
        if name in ["int", "float", "bool", "str", "list", "tuple", "set", "dict", "None"]:
            return ""
        if "." in name:
            name = name.split(".")[-1]

        return name

    async def get_mermaid_sequence_view_versions(self) -> List[(str, str)]:
        """Returns all versioned Markdown sequence diagrams with their corresponding graph repository keys."""
        sequence_views = []
        rows = await self.graph_db.select(predicate=GraphKeyword.HAS_SEQUENCE_VIEW_VER)
        for r in rows:
            sequence_views.append((r.subject, r.object_))
        return sequence_views
