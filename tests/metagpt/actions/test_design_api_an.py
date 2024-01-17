#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_design_api_an.py
"""
import pytest

from metagpt.actions.action_node import ActionNode, dict_to_markdown
from metagpt.actions.design_api import NEW_REQ_TEMPLATE
from metagpt.actions.design_api_an import REFINED_DESIGN_NODES
from metagpt.llm import LLM
from tests.data.incremental_dev_project.mock import (
    DESIGN_SAMPLE,
    REFINED_DESIGN_JSON,
    REFINED_PRD_JSON,
)


@pytest.fixture()
def llm():
    return LLM()


@pytest.mark.asyncio
async def test_write_design_an(mocker):
    root = ActionNode.from_children(
        "RefinedDesignAPI", [ActionNode(key="", expected_type=str, instruction="", example="")]
    )
    root.instruct_content = REFINED_DESIGN_JSON

    mocker.patch("metagpt.actions.design_api_an.REFINED_DESIGN_NODES.fill", return_value=root)
    prompt = NEW_REQ_TEMPLATE.format(old_design=DESIGN_SAMPLE, context=dict_to_markdown(REFINED_PRD_JSON))
    node = await REFINED_DESIGN_NODES.fill(prompt, llm)
    assert "Refined Implementation Approach" in node.instruct_content
    assert "Refined File list" in node.instruct_content
    assert "Refined Data structures and interfaces" in node.instruct_content
    assert "Refined Program call flow" in node.instruct_content
