#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_write_code_plan_an.py
"""
import pytest
from openai._models import BaseModel

from metagpt.actions.action_node import ActionNode
from metagpt.actions.write_code import WriteCode
from metagpt.actions.write_code_plan_an import (
    CODE_PLAN_CONTEXT,
    REFINED_CODE_TEMPLATE,
    WriteCodePlan,
)
from tests.data.incremental_dev_project.mock import (
    DESIGN_SAMPLE,
    NEW_REQUIREMENT_SAMPLE,
    OLD_CODE_SAMPLE,
    PLAN_SAMPLE,
    REFINED_CODE_INPUT_SAMPLE,
    REFINED_CODE_SAMPLE,
    REFINED_DESIGN_JSON,
    REFINED_PRD_JSON,
    REFINED_TASKS_JSON,
    TASKS_SAMPLE,
)


def mock_plan():
    return PLAN_SAMPLE


@pytest.mark.asyncio
async def test_write_code_plan_an(mocker):
    root = ActionNode.from_children(
        "WriteCodePlan", [ActionNode(key="", expected_type=str, instruction="", example="")]
    )
    root.instruct_content = BaseModel()
    root.instruct_content.model_dump = mock_plan
    mocker.patch("metagpt.actions.write_code_plan_an.WriteCodePlan.run", return_value=root)

    write_code_plan = WriteCodePlan()
    context = CODE_PLAN_CONTEXT.format(
        user_requirement=NEW_REQUIREMENT_SAMPLE,
        product_requirement_pools=REFINED_PRD_JSON.get("Refined Requirement Pool", ""),
        design=REFINED_DESIGN_JSON,
        tasks=REFINED_TASKS_JSON,
        code=OLD_CODE_SAMPLE,
    )
    node = await write_code_plan.run(context=context)

    assert "Plan" in node.instruct_content.model_dump()


@pytest.mark.asyncio
async def test_refine_code(mocker):
    mocker.patch("metagpt.actions.write_code.WriteCode.write_code", return_value=REFINED_CODE_SAMPLE)
    prompt = REFINED_CODE_TEMPLATE.format(
        user_requirement=NEW_REQUIREMENT_SAMPLE,
        plan=PLAN_SAMPLE,
        design=DESIGN_SAMPLE,
        tasks=TASKS_SAMPLE,
        code=REFINED_CODE_INPUT_SAMPLE,
        logs="",
        feedback="",
        filename="game.py",
        summary_log="",
    )
    code = await WriteCode().write_code(prompt=prompt)
    assert code
    assert "def" in code
