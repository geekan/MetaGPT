from metagpt.roles.role import Role
from metagpt.ext.opt_code.memory.tree import TreeNode, Tree
from metagpt.ext.opt_code.search_algorithm.tree_search import TreeSearch
from metagpt.ext.opt_code.opt_roles.experimenter import Experimenter
from pydantic import BaseModel

import os

ROOT_PATH = "metagpt/ext/opt_code/optimized"

class MetaAgent(Role):
    search_memory: Tree = None
    search_algorithm: TreeSearch = None
    experimenter: Experimenter = None
    task_name: str = None
    started_search: bool = False

    async def initialize(self, kwargs):
        self.root_path = os.path.join(ROOT_PATH, self.task_name)

        node = self.search_memory.initialize(kwargs, os.path.join(self.root_path, "sela", "nodes")) # TODO: Implement memory initialization
        await self.search_algorithm.initialize(node) # TODO: Implement search algorithm initialization, preparing the context of node
        results = await self.experimenter.initialize(node, kwargs, os.path.join(self.root_path, "roles")) # TODO: Implement experimentor initialization 
        self.search_memory.update_from_child(node, results)
        return node
    
    async def run(self, kwargs):
        for _ in range(kwargs["num_iterations"]):

            if not self.started_search:
                node = await self.initialize(kwargs)
                self.started_search = True
            else:
                node = self.search_algorithm.select_with_strategy(self.search_memory, "greedy") # TODO: Implement memory selection
                if node.depth > 4: # TODO: 这里逻辑没改
                    break

            trial_node, context = await self.search_algorithm.expand_and_prepare(node, self.search_memory) # ADD: Trial Node
            results = await self.experimenter.run(trial_node, context, kwargs["instruction"]) # TODO: Implement experimentor execution

            self.search_algorithm.update(trial_node, results) # TODO: Implement search algorithm update

            self.search_memory.update_from_child(trial_node, results) # TODO: Implement memory update
            # child_node = self.search_memory.add_node(parent=node, results=results)
            # self.search_algorithm.update(child_node, results)

        self.search_memory.report(os.path.join(self.root_path, "report.txt"))