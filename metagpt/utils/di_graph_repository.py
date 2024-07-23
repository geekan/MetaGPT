#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19
@Author  : mashenquan
@File    : di_graph_repository.py
@Desc    : Graph repository based on DiGraph.
    This script defines a graph repository class based on a directed graph (DiGraph), providing functionalities
    specific to handling directed relationships between entities.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import networkx

from metagpt.utils.common import aread, awrite
from metagpt.utils.graph_repository import SPO, GraphRepository


class DiGraphRepository(GraphRepository):
    """Graph repository based on DiGraph."""

    def __init__(self, name: str | Path, **kwargs):
        super().__init__(name=str(name), **kwargs)
        self._repo = networkx.DiGraph()

    async def insert(self, subject: str, predicate: str, object_: str):
        """Insert a new triple into the directed graph repository.

        Args:
            subject (str): The subject of the triple.
            predicate (str): The predicate describing the relationship.
            object_ (str): The object of the triple.

        Example:
            await my_di_graph_repo.insert(subject="Node1", predicate="connects_to", object_="Node2")
            # Adds a directed relationship: Node1 connects_to Node2
        """
        self._repo.add_edge(subject, object_, predicate=predicate)

    async def select(self, subject: str = None, predicate: str = None, object_: str = None) -> List[SPO]:
        """Retrieve triples from the directed graph repository based on specified criteria.

        Args:
            subject (str, optional): The subject of the triple to filter by.
            predicate (str, optional): The predicate describing the relationship to filter by.
            object_ (str, optional): The object of the triple to filter by.

        Returns:
            List[SPO]: A list of SPO objects representing the selected triples.

        Example:
            selected_triples = await my_di_graph_repo.select(subject="Node1", predicate="connects_to")
            # Retrieves directed relationships where Node1 is the subject and the predicate is 'connects_to'.
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

    async def delete(self, subject: str = None, predicate: str = None, object_: str = None) -> int:
        """Delete triples from the directed graph repository based on specified criteria.

        Args:
            subject (str, optional): The subject of the triple to filter by.
            predicate (str, optional): The predicate describing the relationship to filter by.
            object_ (str, optional): The object of the triple to filter by.

        Returns:
            int: The number of triples deleted from the repository.

        Example:
            deleted_count = await my_di_graph_repo.delete(subject="Node1", predicate="connects_to")
            # Deletes directed relationships where Node1 is the subject and the predicate is 'connects_to'.
        """
        rows = await self.select(subject=subject, predicate=predicate, object_=object_)
        if not rows:
            return 0
        for r in rows:
            self._repo.remove_edge(r.subject, r.object_)
        return len(rows)

    def json(self) -> str:
        """Convert the directed graph repository to a JSON-formatted string."""
        m = networkx.node_link_data(self._repo)
        data = json.dumps(m)
        return data

    async def save(self, path: str | Path = None):
        """Save the directed graph repository to a JSON file.

        Args:
            path (Union[str, Path], optional): The directory path where the JSON file will be saved.
                If not provided, the default path is taken from the 'root' key in the keyword arguments.
        """
        data = self.json()
        path = path or self._kwargs.get("root")
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        pathname = Path(path) / self.name
        await awrite(filename=pathname.with_suffix(".json"), data=data, encoding="utf-8")

    async def load(self, pathname: str | Path):
        """Load a directed graph repository from a JSON file."""
        data = await aread(filename=pathname, encoding="utf-8")
        self.load_json(data)

    def load_json(self, val: str):
        """
        Loads a JSON-encoded string representing a graph structure and updates
        the internal repository (_repo) with the parsed graph.

        Args:
            val (str): A JSON-encoded string representing a graph structure.

        Returns:
            self: Returns the instance of the class with the updated _repo attribute.

        Raises:
            TypeError: If val is not a valid JSON string or cannot be parsed into
                       a valid graph structure.
        """
        if not val:
            return self
        m = json.loads(val)
        self._repo = networkx.node_link_graph(m)
        return self

    @staticmethod
    async def load_from(pathname: str | Path) -> GraphRepository:
        """Create and load a directed graph repository from a JSON file.

        Args:
            pathname (Union[str, Path]): The path to the JSON file to be loaded.

        Returns:
            GraphRepository: A new instance of the graph repository loaded from the specified JSON file.
        """
        pathname = Path(pathname)
        graph = DiGraphRepository(name=pathname.stem, root=pathname.parent)
        if pathname.exists():
            await graph.load(pathname=pathname)
        return graph

    @property
    def root(self) -> str:
        """Return the root directory path for the graph repository files."""
        return self._kwargs.get("root")

    @property
    def pathname(self) -> Path:
        """Return the path and filename to the graph repository file."""
        p = Path(self.root) / self.name
        return p.with_suffix(".json")

    @property
    def repo(self):
        """Get the underlying directed graph repository."""
        return self._repo
