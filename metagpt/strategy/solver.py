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
    """AbstractSolver: 用于定义一个抽象求解器，求解器中的搜索空间是 SearchSpace 实例，图是 ActionGraph 实例。"""

    def __init__(self, graph: ActionGraph, search_space: SearchSpace, llm: BaseLLM, context):
        """
        :param graph: ActionGraph 实例
        :param search_space: SearchSpace 实例
        :param llm: BaseLLM
        :param context: Context
        """
        self.graph = graph
        self.search_space = search_space
        self.llm = llm
        self.context = context

    @abstractmethod
    async def solve(self):
        """求解器的求解方法。"""


class NaiveSolver(BaseSolver):
    """NaiveSolver: 直接循序执行给定的 graph"""

    async def solve(self):
        self.graph.topological_sort()
        for key in self.graph.execution_order:
            op = self.graph.nodes[key]
            await op.fill(self.context, self.llm, mode="root")


class TOTSolver(BaseSolver):
    """TOTSolver: 通过拓扑排序执行给定的 graph"""

    async def solve(self):
        raise NotImplementedError


class CodeInterpreterSolver(BaseSolver):
    """CodeInterpreterSolver: 通过代码解释器执行给定的 graph"""

    async def solve(self):
        raise NotImplementedError


class ReActSolver(BaseSolver):
    """ReActSolver: 通过 ReAct 执行给定的 graph"""

    async def solve(self):
        raise NotImplementedError


class IOSolver(BaseSolver):
    """IOSolver: 通过 IO 执行给定的 graph"""

    async def solve(self):
        raise NotImplementedError


class COTSolver(BaseSolver):
    """COTSolver: 通过cot执行给定的 graph"""

    async def solve(self):
        raise NotImplementedError
