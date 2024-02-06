#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_project_management_an.py
"""
import pytest
from openai._models import BaseModel

from metagpt.actions.action_node import ActionNode, dict_to_markdown
from metagpt.actions.project_management import NEW_REQ_TEMPLATE
from metagpt.actions.project_management_an import REFINED_PM_NODE
from metagpt.llm import LLM
from tests.data.incremental_dev_project.mock import (
    REFINED_DESIGN_JSON,
    REFINED_TASKS_JSON,
    TASKS_SAMPLE,
)


@pytest.fixture()
def llm():
    return LLM()


def mock_refined_tasks_json():
    return REFINED_TASKS_JSON


@pytest.mark.asyncio
async def test_project_management_an(mocker):
    root = ActionNode.from_children(
        "RefinedProjectManagement", [ActionNode(key="", expected_type=str, instruction="", example="")]
    )
    root.instruct_content = BaseModel()
    root.instruct_content.model_dump = mock_refined_tasks_json
    mocker.patch("metagpt.actions.project_management_an.REFINED_PM_NODE.fill", return_value=root)

    prompt = NEW_REQ_TEMPLATE.format(old_task=TASKS_SAMPLE, context=dict_to_markdown(REFINED_DESIGN_JSON))
    node = await REFINED_PM_NODE.fill(prompt, llm)

    assert "Refined Logic Analysis" in node.instruct_content.model_dump()
    assert "Refined Task list" in node.instruct_content.model_dump()
    assert "Refined Shared Knowledge" in node.instruct_content.model_dump()
