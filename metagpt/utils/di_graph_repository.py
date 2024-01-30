#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/19
# @Author  : mashenquan
# @File    : di_graph_repository.py
# @Desc    : Graph repository based on DiGraph

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import networkx

from metagpt.utils.common import aread, awrite
from metagpt.utils.graph_repository import SPO, GraphRepository


class DiGraphRepository(GraphRepository):
    """Repository for directed graphs using NetworkX.

    This class provides methods to insert, update, select, and manage graphs
    in a directed graph format using NetworkX.

    Attributes:
        name: A string indicating the name of the repository.
        _repo: A NetworkX DiGraph instance for storing the graph.
    """

    def __init__(self, name: str, **kwargs):
        """Initializes the DiGraphRepository with a name and optional keyword arguments.

        Args:
            name: The name of the graph repository.
            **kwargs: Optional keyword arguments.
        """
        super().__init__(name=name, **kwargs)
        self._repo = networkx.DiGraph()

    async def insert(self, subject: str, predicate: str, object_: str):
        """Inserts a new edge into the graph.

        Args:
            subject: The subject node of the edge.
            predicate: The predicate or relationship of the edge.
            object_: The object node of the edge.
        """
        self._repo.add_edge(subject, object_, predicate=predicate)

    async def upsert(self, subject: str, predicate: str, object_: str):
        """Updates an existing edge or inserts a new one if it doesn't exist.

        Args:
            subject: The subject node of the edge.
            predicate: The predicate or relationship of the edge.
            object_: The object node of the edge.
        """
        pass

    async def update(self, subject: str, predicate: str, object_: str):
        """Updates an existing edge in the graph.

        Args:
            subject: The subject node of the edge.
            predicate: The predicate or relationship of the edge.
            object_: The object node of the edge.
        """
        pass

    async def select(self, subject: str = None, predicate: str = None, object_: str = None) -> List[SPO]:
        """Selects edges from the graph based on provided criteria.

        Args:
            subject: The subject node of the edge (optional).
            predicate: The predicate or relationship of the edge (optional).
            object_: The object node of the edge (optional).

        Returns:
            A list of SPO tuples representing the selected edges.
        """
        result = []
        for s, o, p in self._repo.edges(data="predicate"):
            if subject and subject != s:
                continue
            if predicate and predicate != p:
                continue
            if object_ and object_ != o:
                continue
            result.append(SPO(subject=s, predicate=p, object_=o))
        return result

    def json(self) -> str:
        """Serializes the graph to a JSON string.

        Returns:
            A JSON string representation of the graph.
        """
        m = networkx.node_link_data(self._repo)
        data = json.dumps(m)
        return data

    async def save(self, path: str | Path = None):
        """Saves the graph to a JSON file.

        Args:
            path: The file path or Path object where the graph will be saved. If not provided, uses default path.
        """
        data = self.json()
        path = path or self._kwargs.get("root")
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        pathname = Path(path) / self.name
        await awrite(filename=pathname.with_suffix(".json"), data=data, encoding="utf-8")

    async def load(self, pathname: str | Path):
        """Loads the graph from a JSON file.

        Args:
            pathname: The file path or Path object from which the graph will be loaded.
        """
        data = await aread(filename=pathname, encoding="utf-8")
        m = json.loads(data)
        self._repo = networkx.node_link_graph(m)

    @staticmethod
    async def load_from(pathname: str | Path) -> GraphRepository:
        """Loads a graph from a JSON file and returns a new DiGraphRepository instance.

        Args:
            pathname: The file path or Path object from which the graph will be loaded.

        Returns:
            A new instance of DiGraphRepository loaded with the graph.
        """
        pathname = Path(pathname)
        name = pathname.with_suffix("").name
        root = pathname.parent
        graph = DiGraphRepository(name=name, root=root)
        if pathname.exists():
            await graph.load(pathname=pathname)
        return graph

    @property
    def root(self) -> str:
        """The root directory for the graph repository.

        Returns:
            The root directory as a string.
        """
        return self._kwargs.get("root")

    @property
    def pathname(self) -> Path:
        """The full pathname for the graph JSON file.

        Returns:
            The Path object representing the full pathname.
        """
        p = Path(self.root) / self.name
        return p.with_suffix(".json")
