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
    """Graph repository based on DiGraph.

    This class represents a graph repository that utilizes a directed graph (DiGraph) to manage relationships
    between entities. It inherits from the GraphRepository class, providing a common interface for graph repositories.

    Attributes:
        _repo (DiGraph): The underlying directed graph representing the repository.

    Methods:
        insert: Insert a new triple into the graph repository.
        select: Retrieve triples from the graph repository based on specified criteria.
        delete: Delete triples from the graph repository based on specified criteria.
        save: Save any changes made to the graph repository.
        name: Get the name of the graph repository.

    Example:
        di_graph_repo = DiGraphRepository(name="MyDiGraphRepo")
        di_graph_repo.insert(subject="Node1", predicate="connects_to", object_="Node2")
        # Represents a directed relationship: Node1 connects_to Node2

    Note:
        This class extends the GraphRepository class and is specifically designed for managing directed relationships
        using a DiGraph.

    """

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self._repo = networkx.DiGraph()

    async def insert(self, subject: str, predicate: str, object_: str):
        """Insert a new triple into the directed graph repository.

        This method adds a new triple to the underlying directed graph. The triple consists of a subject, a predicate
        describing the relationship, and an object.

        Args:
            subject (str): The subject of the triple.
            predicate (str): The predicate describing the relationship.
            object_ (str): The object of the triple.

        Returns:
            None

        Raises:
            SomeException: Describe any exceptions that might be raised during the insertion process.

        Example:
            await my_di_graph_repo.insert(subject="Node1", predicate="connects_to", object_="Node2")
            # Adds a directed relationship: Node1 connects_to Node2

        Note:
            Implementations should handle the insertion of triples into the directed graph.

        """
        self._repo.add_edge(subject, object_, predicate=predicate)

    async def select(self, subject: str = None, predicate: str = None, object_: str = None) -> List[SPO]:
        """Retrieve triples from the directed graph repository based on specified criteria.

        This method queries the directed graph repository and retrieves triples that match the specified criteria.

        Args:
            subject (str, optional): The subject of the triple to filter by.
            predicate (str, optional): The predicate describing the relationship to filter by.
            object_ (str, optional): The object of the triple to filter by.

        Returns:
            List[SPO]: A list of SPO objects representing the selected triples.

        Raises:
            SomeException: Describe any exceptions that might be raised during the selection process.

        Example:
            selected_triples = await my_di_graph_repo.select(subject="Node1", predicate="connects_to")
            # Retrieves directed relationships where Node1 is the subject and the predicate is 'connects_to'.

        Note:
            Implementations should handle the selection of triples from the directed graph.

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

        This method removes triples from the directed graph repository that match the specified criteria.

        Args:
            subject (str, optional): The subject of the triple to filter by.
            predicate (str, optional): The predicate describing the relationship to filter by.
            object_ (str, optional): The object of the triple to filter by.

        Returns:
            int: The number of triples deleted from the repository.

        Raises:
            SomeException: Describe any exceptions that might be raised during the deletion process.

        Example:
            deleted_count = await my_di_graph_repo.delete(subject="Node1", predicate="connects_to")
            # Deletes directed relationships where Node1 is the subject and the predicate is 'connects_to'.

        Note:
            Implementations should handle the deletion of triples from the directed graph.

        """
        rows = await self.select(subject=subject, predicate=predicate, object_=object_)
        if not rows:
            return 0
        for r in rows:
            self._repo.remove_edge(r.subject, r.object_)
        return len(rows)

    def json(self) -> str:
        """Convert the directed graph repository to a JSON-formatted string.

        This method converts the underlying directed graph repository to a JSON-formatted string using the node-link data
        format.

        Returns:
            str: A JSON-formatted string representing the directed graph repository.

        Example:
            json_data = my_di_graph_repo.json()
            # Retrieves a JSON-formatted string representing the directed graph repository.

        Note:
            The resulting JSON string can be used for serialization or data interchange.

        """
        m = networkx.node_link_data(self._repo)
        data = json.dumps(m)
        return data

    async def save(self, path: str | Path = None):
        """Save the directed graph repository to a JSON file.

        This method converts the underlying directed graph repository to a JSON-formatted string and saves it to a file.
        The file is saved with the name of the graph repository and a ".json" extension.

        Args:
            path (Union[str, Path], optional): The directory path where the JSON file will be saved.
                If not provided, the default path is taken from the 'root' key in the keyword arguments.

        Returns:
            None

        Example:
            await my_di_graph_repo.save(path="/path/to/save")
            # Saves the directed graph repository to a JSON file at the specified path.

        Note:
            The saved JSON file contains the node-link data representing the directed graph.

        """
        data = self.json()
        path = path or self._kwargs.get("root")
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        pathname = Path(path) / self.name
        await awrite(filename=pathname.with_suffix(".json"), data=data, encoding="utf-8")

    async def load(self, pathname: str | Path):
        """Load a directed graph repository from a JSON file.

        This method reads a JSON file containing node-link data representing a directed graph and loads it into the
        directed graph repository.

        Args:
            pathname (Union[str, Path]): The path to the JSON file to be loaded.

        Returns:
            None

        Example:
            await my_di_graph_repo.load(pathname="/path/to/load/my_graph.json")
            # Loads a directed graph repository from the specified JSON file.

        Note:
            The JSON file should contain node-link data compatible with the format produced by the 'json' method.

        """
        data = await aread(filename=pathname, encoding="utf-8")
        m = json.loads(data)
        self._repo = networkx.node_link_graph(m)

    @staticmethod
    async def load_from(pathname: str | Path) -> GraphRepository:
        """Create and load a directed graph repository from a JSON file.

        This class method creates a new instance of a graph repository and loads it from a JSON file containing node-link
        data representing a directed graph.

        Args:
            pathname (Union[str, Path]): The path to the JSON file to be loaded.

        Returns:
            GraphRepository: A new instance of the graph repository loaded from the specified JSON file.

        Example:
            loaded_repo = await GraphRepository.load_from(pathname="/path/to/load/my_graph.json")
            # Creates and loads a directed graph repository from the specified JSON file.

        Note:
            The JSON file should contain node-link data compatible with the format produced by the 'json' method.

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
        """Return the root directory path for the graph repository files.

        Returns:
            str: The root directory path.

        Example:
            root_path = my_graph_repo.root
            # Retrieves the root directory path for the graph repository files.

        Note:
            This property provides the directory path where graph repository files are saved or loaded.

        """
        return self._kwargs.get("root")

    @property
    def pathname(self) -> Path:
        """Return the path and filename to the graph repository file.

        Returns:
            Path: The path and filename to the graph repository file.

        Example:
            file_path = my_graph_repo.pathname
            # Retrieves the path and filename to the graph repository file.

        Note:
            This property provides the full path, including the filename, to the graph repository file.

        """
        p = Path(self.root) / self.name
        return p.with_suffix(".json")

    @property
    def repo(self):
        """Get the underlying directed graph repository.

        Returns:
            networkx.DiGraph: The directed graph repository.

        Example:
            my_di_graph = my_graph_repo.repo
            # Retrieves the underlying directed graph repository.

        Note:
            This property provides direct access to the networkx.DiGraph instance used by the graph repository.

        """
        return self._repo
