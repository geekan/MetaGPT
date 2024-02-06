#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_write_prd_an.py
"""
import pytest
from openai._models import BaseModel

from metagpt.actions.action_node import ActionNode
from metagpt.actions.write_prd import NEW_REQ_TEMPLATE
from metagpt.actions.write_prd_an import REFINED_PRD_NODE
from metagpt.llm import LLM
from tests.data.incremental_dev_project.mock import (
    NEW_REQUIREMENT_SAMPLE,
    PRD_SAMPLE,
    REFINED_PRD_JSON,
)


@pytest.fixture()
def llm():
    return LLM()


def mock_refined_prd_json():
    return REFINED_PRD_JSON


@pytest.mark.asyncio
async def test_write_prd_an(mocker):
    root = ActionNode.from_children("RefinedPRD", [ActionNode(key="", expected_type=str, instruction="", example="")])
    root.instruct_content = BaseModel()
    root.instruct_content.model_dump = mock_refined_prd_json
    mocker.patch("metagpt.actions.write_prd_an.REFINED_PRD_NODE.fill", return_value=root)

    prompt = NEW_REQ_TEMPLATE.format(
        requirements=NEW_REQUIREMENT_SAMPLE,
        old_prd=PRD_SAMPLE,
    )
    node = await REFINED_PRD_NODE.fill(prompt, llm)

    assert "Refined Requirements" in node.instruct_content.model_dump()
    assert "Refined Product Goals" in node.instruct_content.model_dump()
    assert "Refined User Stories" in node.instruct_content.model_dump()
    assert "Refined Requirement Analysis" in node.instruct_content.model_dump()
    assert "Refined Requirement Pool" in node.instruct_content.model_dump()
