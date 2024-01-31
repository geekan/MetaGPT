#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/30 13:52
@Author  : alexanderwu
@File    : action_graph.py
"""
from __future__ import annotations

# from metagpt.actions.action_node import ActionNode


class ActionGraph:
    """ActionGraph: 用于定义一个图，图中的节点是 ActionNode 实例，节点间的依赖关系是有向边。"""

    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.execution_order = []

    def add_node(self, node):
        """
        添加一个节点到图中。
        :param node: ActionNode 实例
        """
        self.nodes[node.key] = node

    def add_edge(self, from_node: "ActionNode", to_node: "ActionNode"):
        """
        定义节点间的依赖关系。
        :param from_node: 节点标识
        :param to_node: 节点标识
        """
        if from_node.key not in self.edges:
            self.edges[from_node.key] = []
        self.edges[from_node.key].append(to_node.key)
        from_node.add_next(to_node)
        to_node.add_prev(from_node)

    def topological_sort(self):
        """
        实现拓扑排序来确定执行顺序。
        """
        visited = set()
        stack = []

        def visit(k):
            if k not in visited:
                visited.add(k)
                if k in self.edges:
                    for next_node in self.edges[k]:
                        visit(next_node)
                stack.insert(0, k)

        for key in self.nodes:
            visit(key)

        self.execution_order = stack
