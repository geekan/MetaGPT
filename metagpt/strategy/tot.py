# -*- coding: utf-8 -*-
# @Date    : 12/23/2023 4:51 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from __future__ import annotations

import asyncio
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.strategy.base import ThoughtNode, ThoughtTree
from metagpt.strategy.tot_schema import MethodSelect, Strategy, ThoughtSolverConfig
from metagpt.utils.common import CodeParser

OUTPUT_FORMAT = """
Each output should be strictly a list of nodes, in json format, like this:
```json
    [
        {
            "node_id": str = "unique identifier for a solution, can be an ordinal",
            "node_state_instruction": "specified sample of solution",
        },
        ...
    ]
```
"""


class ThoughtSolverBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    thought_tree: Optional[ThoughtTree] = Field(default=None)
    llm: BaseLLM = Field(default_factory=LLM, exclude=True)
    config: ThoughtSolverConfig = Field(default_factory=ThoughtSolverConfig)

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.llm.use_system_prompt = False

    async def solve(self, init_prompt):
        """
        Solve method for subclasses to implement.
        """
        raise NotImplementedError("Subclasses must implement the solve method")

    async def generate_thoughts(self, current_state="", current_node=None) -> List[ThoughtNode]:
        """
        Generate children thoughts based on the current state.

        Args:
            current_state (str): The current state for which thoughts are generated.
            current_node (ThoughtNode): The current node in the thought tree.

        Returns:
            List[ThoughtNode]: List of nodes representing the generated thoughts.
        """
        state_prompt = self.config.parser.propose(
            current_state=current_state, **{"n_generate_sample": self.config.n_generate_sample}
        )
        rsp = await self.llm.aask(msg=state_prompt + "\n" + OUTPUT_FORMAT)
        thoughts = CodeParser.parse_code(block="", text=rsp)
        thoughts = eval(thoughts)
        # fixme 避免不跟随，生成过多nodes
        # valid_thoughts = [_node for idx, _node in enumerate(thoughts) if idx < self.n_generate_sample]
        return self.thought_tree.update_node(thoughts, current_node=current_node)

    async def evaluate_node(self, node, parent_value) -> None:
        """
        Evaluate a node and update its status and value.

        Args:
            node (ThoughtNode): The node to be evaluated.
            parent_value (float): The parent node's value.

        Returns:
            None
        """
        eval_prompt = self.config.parser.value(input=node.name, **{"node_id": node.id})
        evaluation = await self.llm.aask(msg=eval_prompt)

        value = self.config.evaluator(evaluation, **{"node_id": node.id})
        status = self.config.evaluator.status_verify(value)

        node.update_valid_status(status=status)
        # 累计分数
        node.update_value(parent_value + value)

    def select_nodes(self, thought_nodes: List[ThoughtNode]) -> List[ThoughtNode]:
        """
        Select nodes based on the configured selection method.

        Args:
            thought_nodes (List[ThoughtNode]): List of nodes to be selected.

        Returns:
            List[ThoughtNode]: List of selected nodes.
        """
        # nodes to be selected
        nodes = []
        if self.config.method_select == MethodSelect.SAMPLE:
            raise NotImplementedError
        elif self.config.method_select == MethodSelect.GREEDY:
            nodes = sorted(thought_nodes, key=lambda x: x.value, reverse=True)[: self.config.n_select_sample]
        for node in thought_nodes:
            if node not in nodes:
                node.parent = None  # 从树中删除节点
        return nodes

    def update_solution(self):
        """
        Select the result with the highest score.

        Returns:
            - List[ThoughtNode]: List of nodes representing the best solution.
            - List[str]: List of node names forming the best solution path.
        """
        best_node = max(self.thought_tree.all_nodes, key=lambda x: x.value, default=None)
        best_solution_path = self.thought_tree.parse_node_path(best_node)
        return [best_node], best_solution_path


class BFSSolver(ThoughtSolverBase):
    async def solve(self, init_prompt=""):
        """
        Solve the problem using Breadth-First Search (BFS) strategy.

        Args:
            init_prompt (str): The initial prompt for the solver.

        Returns:
            List[str]: The best solution path obtained through BFS.
        """
        root = ThoughtNode(init_prompt)
        self.thought_tree = ThoughtTree(root)
        current_nodes = [root]
        for step in range(self.config.max_steps):
            solutions = await self._bfs_build(current_nodes)

            selected_nodes = self.select_nodes(solutions)
            current_nodes = selected_nodes

            self.thought_tree.show()

        best_solution, best_solution_path = self.update_solution()
        logger.info(f"best solution is: {best_solution_path}")
        return best_solution_path

    async def _bfs_build(self, current_nodes):
        """
        Build the thought tree using Breadth-First Search (BFS) strategy.

        Args:
            current_nodes (List[ThoughtNode]): Current nodes to expand.

        Returns:
            List[ThoughtNode]: The solutions obtained after expanding the current nodes.
        """
        tasks = []
        for node in current_nodes:
            current_state = self.config.parser(node.name)
            current_value = node.value
            tasks.append(self.generate_and_evaluate_nodes(current_state, current_value, node))

        thought_nodes_list = await asyncio.gather(*tasks)
        solutions = [child_node for thought_nodes in thought_nodes_list for child_node in thought_nodes]
        return solutions

    async def generate_and_evaluate_nodes(self, current_state, current_value, node):
        thought_nodes = await self.generate_thoughts(current_state, current_node=node)
        await asyncio.gather(
            *(self.evaluate_node(child_node, parent_value=current_value) for child_node in thought_nodes)
        )
        return thought_nodes


class DFSSolver(ThoughtSolverBase):
    async def _dfs(self, root_node):
        """
        Perform Depth-First Search (DFS) on the thought tree.

        Args:
            root_node (ThoughtNode): The root node of the thought tree.

        Returns:
            List[str]: The solution path obtained through DFS.
        """
        impossible_state_cnt = 0
        node = root_node
        for step in range(self.max_steps):
            current_state = self.config.parser(node.name)
            current_value = node.value
            thought_nodes = await self.generate_thoughts(current_state, current_node=node)
            await self.evaluate_node(thought_nodes[0], parent_value=current_value)
            if thought_nodes[0].valid_status is False:
                impossible_state_cnt += 1
            if impossible_state_cnt >= 2:
                logger.info("impossible state reached, break")
                break
            node = thought_nodes[0]
        _solution_path = self.thought_tree.parse_node_path(node)
        self.thought_tree.show()

        return _solution_path

    async def solve(self, init_prompt="", root=ThoughtNode("")):
        """
        Solve the problem using Depth-First Search (DFS) strategy.

        Args:
            init_prompt (str): The initial prompt for the solver.

        Returns:
            List[str]: The best solution path obtained through DFS.
        """
        root = ThoughtNode(init_prompt)
        self.thought_tree = ThoughtTree(root)
        for n in range(self.config.n_solution_sample):
            # fixme: 需要产生回退，当前节点不可用时回退到父节点，产生新的节点继续探索
            await self._dfs(root)

        best_solution, best_solution_path = self.update_solution()
        logger.info(f"best solution is: {best_solution_path}")
        return best_solution_path


class MCTSSolver(ThoughtSolverBase):
    async def solve(self, init_prompt=""):
        raise NotImplementedError


class TreeofThought(BaseModel):
    config: ThoughtSolverConfig = Field(default_factory=ThoughtSolverConfig)
    solver: ThoughtSolverBase = Field(default_factory=ThoughtSolverBase)
    strategy: Strategy = Field(default=Strategy.BFS)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._initialize_solver(self.strategy)

    def _initialize_solver(self, strategy):
        """
        Initialize the solver based on the chosen strategy.

        Args:
            strategy (Strategy): The strategy to use for solving.

        Returns:
            ThoughtSolverBase: An instance of the appropriate solver.
        """
        if strategy == Strategy.BFS:
            self.solver = BFSSolver(config=self.config)
        elif strategy == Strategy.DFS:
            self.solver = DFSSolver(config=self.config)
        elif strategy == Strategy.MCTS:
            self.solver = MCTSSolver(config=self.config)
        else:
            raise NotImplementedError(f"Invalid strategy: {strategy}, only support BFS/DFS/MCTS currently!")

    async def solve(self, init_prompt=""):
        """
        Solve the problem using the specified strategy.

        Args:
            init_prompt (str): The initial prompt for the solver.
            strategy (str): The strategy to use for solving.

        Returns:
            Any: The solution obtained using the selected strategy.
        """
        await self.solver.solve(init_prompt)
