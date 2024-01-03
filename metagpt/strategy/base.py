# -*- coding: utf-8 -*-
# @Date    : 12/25/2023 9:16 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from abc import ABC
from typing import List

from anytree import Node, RenderTree
from pydantic import BaseModel


class BaseParser(BaseModel, ABC):
    def __call__(self, *args, **kwargs):
        raise NotImplementedError

    def propose(self, current_state: str, **kwargs) -> str:
        raise NotImplementedError

    def sample(self, current_state: str, **kwargs) -> str:
        raise NotImplementedError

    def value(self, input: str, **kwargs) -> str:
        raise NotImplementedError


class BaseEvaluator(BaseModel, ABC):
    def __call__(self, *args, **kwargs):
        raise NotImplementedError

    def status_verify(self, *args, **kwargs):
        raise NotImplementedError


class ThoughtNode(Node):
    """A node representing a thought in the thought tree."""

    name: str = ""
    value: int = 0
    id: int = 0
    valid_status: bool = True

    def update_value(self, value) -> None:
        """Update the value of the thought node."""
        self.value = value

    def update_valid_status(self, status) -> None:
        """Update the validity status of the thought node."""
        self.valid_status = status


class ThoughtTree(RenderTree):
    """A tree structure to represent thoughts."""

    @property
    def all_nodes(self) -> List[ThoughtNode]:
        """
        Get a list of all nodes in the thought tree.

        Returns:
            List[ThoughtNode]: A list containing all nodes in the thought tree.
        """
        all_nodes = [node for _, _, node in self]
        return all_nodes

    def update_node(self, thought: List[dict] = [], current_node: ThoughtNode = None) -> List[ThoughtNode]:
        """
        Update the tree with new thoughts.

        Args:
            thought (List[dict]): A list of dictionaries representing thought information.
            current_node (ThoughtNode): The current node under which new thoughts will be added.

        Returns:
            List[ThoughtNode]: A list of ThoughtNode instances representing the updated tree nodes.
        """
        nodes = []
        for node_info in thought:
            node = ThoughtNode(
                name=node_info["node_state_instruction"], parent=current_node, id=int(node_info["node_id"])
            )
            nodes.append(node)
        return nodes

    def parse_node_path(self, node) -> List[str]:
        """
        Parse and retrieve the hierarchical path of the given thought node.

        This method traverses the parent nodes of the provided 'node' and constructs
        the full path from the root node to the given node.

        Args:
            node: The thought node for which the hierarchical path needs to be parsed.

        Returns:
            List[str]: A list representing the full hierarchical path of the given thought node.
                       The list is ordered from the root node to the provided node.
        """
        full_node_path = []
        while node is not None:
            full_node_path.append(node.name)
            node = node.parent
        full_node_path.reverse()
        return full_node_path

    def show(self) -> None:
        """Print the updated tree."""
        print("\nUpdated Tree:")
        for pre, _, node in self:
            print(f"{pre}{node.name}, value: {node.value}, valid_status: {node.valid_status}")
