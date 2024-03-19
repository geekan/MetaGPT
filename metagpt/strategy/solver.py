#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/30 17:13
@Author  : alexanderwu
@File    : solver.py
"""
from abc import abstractmethod

from metagpt.actions.action_graph import ActionGraph
from metagpt.provider.base_llm import BaseLLM
from metagpt.strategy.search_space import SearchSpace


class BaseSolver:
    """AbstractSolver: defines the interface of a solver."""

    def __init__(self, graph: ActionGraph, search_space: SearchSpace, llm: BaseLLM, context):
        """
        :param graph: ActionGraph
        :param search_space: SearchSpace
        :param llm: BaseLLM
        :param context: Context
        """
        self.graph = graph
        self.search_space = search_space
        self.llm = llm
        self.context = context

    @abstractmethod
    async def solve(self):
        """abstract method to solve the problem."""


class NaiveSolver(BaseSolver):
    """NaiveSolver: Iterate all the nodes in the graph and execute them one by one."""

    async def solve(self):
        self.graph.topological_sort()
        for key in self.graph.execution_order:
            op = self.graph.nodes[key]
            await op.fill(self.context, self.llm, mode="root")


class TOTSolver(BaseSolver):
    """TOTSolver: Tree of Thought"""

    async def solve(self):
        raise NotImplementedError


class DataInterpreterSolver(BaseSolver):
    """DataInterpreterSolver: Write&Run code in the graph"""

    async def solve(self):
        raise NotImplementedError


class ReActSolver(BaseSolver):
    """ReActSolver: ReAct algorithm"""

    async def solve(self):
        raise NotImplementedError


class IOSolver(BaseSolver):
    """IOSolver: use LLM directly to solve the problem"""

    async def solve(self):
        raise NotImplementedError


class COTSolver(BaseSolver):
    """COTSolver: Chain of Thought"""

    async def solve(self):
        raise NotImplementedError
