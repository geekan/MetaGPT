# -*- coding: utf-8 -*-
# @Date    : 12/25/2023 9:16 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from typing import List

from pydantic import BaseModel
from anytree import Node, RenderTree



class BaseParser(BaseModel):
    def __call__(self, *args, **kwargs):
        raise NotImplementedError
    
    def propose(self, current_state: str, **kwargs) -> str:
        raise NotImplementedError
    
    def sample(self, current_state: str, **kwargs) -> str:
        raise NotImplementedError
    
    def value(self, input: str, **kwargs) -> str:
        raise NotImplementedError


class BaseEvaluator(BaseModel):
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
        """Get a list of all nodes in the thought tree."""
        all_nodes = [node for _, _, node in self]
        return all_nodes
    
    def update_node(self, thought: List[dict] = [], current_node: ThoughtNode = None) -> List[ThoughtNode]:
        """Update the tree with new thoughts."""
        nodes = []
        for node_info in thought:
            node = ThoughtNode(name=node_info["node_state_instruction"], parent=current_node,
                               id=int(node_info["node_id"]))
            nodes.append(node)
        return nodes
    
    def parse_node_path(self, node) -> List[str]:
        """Parse the path of the given thought node."""
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