#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_project_management_an.py
"""
import pytest

from metagpt.actions.action_node import ActionNode, dict_to_markdown
from metagpt.actions.project_management import NEW_REQ_TEMPLATE
from metagpt.actions.project_management_an import REFINED_PM_NODES
from metagpt.llm import LLM
from tests.data.incremental_dev_project.mock import (
    REFINED_DESIGN_JSON,
    REFINED_TASKS_JSON,
    TASKS_SAMPLE,
)


@pytest.fixture()
def llm():
    return LLM()


@pytest.mark.asyncio
async def test_project_management_an(mocker):
    root = ActionNode.from_children(
        "RefinedProjectManagement", [ActionNode(key="", expected_type=str, instruction="", example="")]
    )
    root.instruct_content = REFINED_TASKS_JSON

    mocker.patch("metagpt.actions.project_management_an.REFINED_PM_NODES.fill", return_value=root)

    prompt = NEW_REQ_TEMPLATE.format(old_tasks=TASKS_SAMPLE, context=dict_to_markdown(REFINED_DESIGN_JSON))
    node = await REFINED_PM_NODES.fill(prompt, llm)
    assert node.instruct_content
    assert "Refined Logic Analysis" in node.instruct_content
    assert "Refined Task list" in node.instruct_content
    assert "Refined Shared Knowledge" in node.instruct_content
