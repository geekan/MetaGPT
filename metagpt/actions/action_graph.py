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
    """ActionGraph: a directed graph to represent the dependency between actions."""

    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.execution_order = []

    def add_node(self, node):
        """Add a node to the graph"""
        self.nodes[node.key] = node

    def add_edge(self, from_node: "ActionNode", to_node: "ActionNode"):
        """Add an edge to the graph"""
        if from_node.key not in self.edges:
            self.edges[from_node.key] = []
        self.edges[from_node.key].append(to_node.key)
        from_node.add_next(to_node)
        to_node.add_prev(from_node)

    def topological_sort(self):
        """Topological sort the graph"""
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
