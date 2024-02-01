#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/31 13:54
@Author  : alexanderwu
@File    : test_solver.py
"""
import pytest

from metagpt.actions.action_graph import ActionGraph
from metagpt.llm import LLM
from metagpt.strategy.search_space import SearchSpace
from metagpt.strategy.solver import NaiveSolver


@pytest.mark.asyncio
async def test_solver():
    from metagpt.actions.write_prd_an import (
        COMPETITIVE_ANALYSIS,
        ISSUE_TYPE,
        PRODUCT_GOALS,
        REQUIREMENT_POOL,
    )

    graph = ActionGraph()
    graph.add_node(ISSUE_TYPE)
    graph.add_node(PRODUCT_GOALS)
    graph.add_node(COMPETITIVE_ANALYSIS)
    graph.add_node(REQUIREMENT_POOL)
    graph.add_edge(ISSUE_TYPE, PRODUCT_GOALS)
    graph.add_edge(PRODUCT_GOALS, COMPETITIVE_ANALYSIS)
    graph.add_edge(PRODUCT_GOALS, REQUIREMENT_POOL)
    graph.add_edge(COMPETITIVE_ANALYSIS, REQUIREMENT_POOL)
    search_space = SearchSpace()
    llm = LLM()
    context = "Create a 2048 game"
    solver = NaiveSolver(graph, search_space, llm, context)
    await solver.solve()

    print("## graph.nodes")
    print(graph.nodes)
    for k, v in graph.nodes.items():
        print(f"{v.key} | prevs: {[i.key for i in v.prevs]} | nexts: {[i.key for i in v.nexts]}")

    assert len(graph.nodes) == 4
    assert len(graph.execution_order) == 4
    assert graph.execution_order == [ISSUE_TYPE.key, PRODUCT_GOALS.key, COMPETITIVE_ANALYSIS.key, REQUIREMENT_POOL.key]
