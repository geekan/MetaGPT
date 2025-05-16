from abc import ABC, abstractmethod
from pydantic import BaseModel
from metagpt.ext.opt_code.memory.tree import TreeNode
import numpy as np


class TreeSearch(ABC):
    """Base class for tree-based search algorithms."""
    def __init__(self, configs):
        """
        Initialize the TreeSearch base class.
        
        Args:
            configs: Dictionary containing configurations for the search algorithm
        """
        self.configs = configs

    async def initialize(self, node):
        """Initialize the search with root node."""
        self.global_context = {}
        await self._initialize(node, self.global_context)

    @abstractmethod
    async def _initialize(self, node, global_context):
        """Initialize the search with root node."""
        pass

    def select_with_strategy(self, memory, strategy: str = None):
        """
        Select a node from the memory to process based on the strategy.
        
        Args:
            memory: The memory to select a node from
            strategy: The strategy to use for selecting the node
        """
        match strategy:
            case "random":
                return np.random.choice(memory.node_list)
            case "greedy":
                # return the node with the highest reward
                return max(memory.node_list, key=lambda x: x.reward)
            case _:
                return self.select(memory)


    @abstractmethod
    def select(self, memory):
        """
        Select a node from the memory to process.
        
        Args:
            memory: The memory to select a node from
        """
        pass
    
    async def expand_and_prepare(self, node, memory):
        trial_node = await self._expand(node, memory)

        context = self._prepare(node)
        return trial_node, context
    
    @abstractmethod
    async def _expand(self, node):
        pass
    
    @abstractmethod
    def _prepare(self, node) -> dict:
        """
        Prepare the context for agent to process the node.
        
        Args:
            node: The node to prepare context for
            context: Dictionary containing information needed by the agent
        """
        pass

    def update(self, node: TreeNode, results):
        """
        Update the node with the results of the execution.
        
        Args:
            node: The node to update
            results: Dictionary containing the results of the execution
        """
        self._update_global_context(node, results) # TODO: Implement global context update

    @abstractmethod
    def _update_global_context(self, node, results):
        """
        Update the global context with the results of the execution.
        """
        pass

        