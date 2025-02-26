#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_cost_manager.py
"""
import pytest

from metagpt.utils.cost_manager import CostManager


def test_cost_manager():
    cm = CostManager(total_budget=20)
    cm.update_cost(prompt_tokens=1000, completion_tokens=100, model="gpt-4-turbo")
    assert cm.get_total_prompt_tokens() == 1000
    assert cm.get_total_completion_tokens() == 100
    assert cm.get_total_cost() == 0.013
    cm.update_cost(prompt_tokens=100, completion_tokens=10, model="gpt-4-turbo")
    assert cm.get_total_prompt_tokens() == 1100
    assert cm.get_total_completion_tokens() == 110
    assert cm.get_total_cost() == 0.0143
    cost = cm.get_costs()
    assert cost
    assert cost.total_cost == cm.get_total_cost()
    assert cost.total_prompt_tokens == cm.get_total_prompt_tokens()
    assert cost.total_completion_tokens == cm.get_total_completion_tokens()
    assert cost.total_budget == 20


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
