#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_design_api_an.py
"""
import pytest
from openai._models import BaseModel

from metagpt.actions.action_node import ActionNode, dict_to_markdown
from metagpt.actions.design_api import NEW_REQ_TEMPLATE
from metagpt.actions.design_api_an import REFINED_DESIGN_NODE
from metagpt.llm import LLM
from tests.data.incremental_dev_project.mock import (
    DESIGN_SAMPLE,
    REFINED_DESIGN_JSON,
    REFINED_PRD_JSON,
)


@pytest.fixture()
def llm():
    return LLM()


def mock_refined_design_json():
    return REFINED_DESIGN_JSON


@pytest.mark.asyncio
async def test_write_design_an(mocker):
    root = ActionNode.from_children(
        "RefinedDesignAPI", [ActionNode(key="", expected_type=str, instruction="", example="")]
    )
    root.instruct_content = BaseModel()
    root.instruct_content.model_dump = mock_refined_design_json
    mocker.patch("metagpt.actions.design_api_an.REFINED_DESIGN_NODE.fill", return_value=root)

    prompt = NEW_REQ_TEMPLATE.format(old_design=DESIGN_SAMPLE, context=dict_to_markdown(REFINED_PRD_JSON))
    node = await REFINED_DESIGN_NODE.fill(prompt, llm)

    assert "Refined Implementation Approach" in node.instruct_content.model_dump()
    assert "Refined File list" in node.instruct_content.model_dump()
    assert "Refined Data structures and interfaces" in node.instruct_content.model_dump()
    assert "Refined Program call flow" in node.instruct_content.model_dump()
