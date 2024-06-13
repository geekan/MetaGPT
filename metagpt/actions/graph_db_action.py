"""
graph_db_action.py

This module defines the GraphDBAction class, which interacts with a graph database.

Classes:
    GraphDBAction: An action class that interacts with a graph database.

Usage Example:
    action = GraphDBAction()
    await action.load_graph_db('path/to/graph_db')

    action = GraphDBAction(graph_db=external_graph_db)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from metagpt.actions import Action
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.graph_repository import GraphRepository


class GraphDBAction(Action):
    """
    An action class that interacts with a graph database.

    Attributes:
        graph_db (Optional[GraphRepository]): The graph database instance.
    """

    graph_db: Optional[GraphRepository] = None

    async def load_graph_db(self, pathname: str | Path):
        """
        Asynchronously loads the graph database from the specified path.

        Args:
            pathname (str | Path): The path to the graph database file.
        """
        self.graph_db = await DiGraphRepository.load_from(pathname)
