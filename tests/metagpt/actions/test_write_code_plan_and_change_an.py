#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_write_code_plan_and_change_an.py
"""
import pytest
from openai._models import BaseModel

from metagpt.actions.action_node import ActionNode
from metagpt.actions.write_code import WriteCode
from metagpt.actions.write_code_plan_and_change_an import (
    REFINED_TEMPLATE,
    WriteCodePlanAndChange,
)
from metagpt.schema import CodePlanAndChangeContext
from tests.data.incremental_dev_project.mock import (
    CODE_PLAN_AND_CHANGE_SAMPLE,
    DESIGN_SAMPLE,
    NEW_REQUIREMENT_SAMPLE,
    REFINED_CODE_INPUT_SAMPLE,
    REFINED_CODE_SAMPLE,
    TASKS_SAMPLE,
)


def mock_code_plan_and_change():
    return CODE_PLAN_AND_CHANGE_SAMPLE


@pytest.mark.asyncio
async def test_write_code_plan_and_change_an(mocker):
    root = ActionNode.from_children(
        "WriteCodePlanAndChange", [ActionNode(key="", expected_type=str, instruction="", example="")]
    )
    root.instruct_content = BaseModel()
    root.instruct_content.model_dump = mock_code_plan_and_change
    mocker.patch("metagpt.actions.write_code_plan_and_change_an.WriteCodePlanAndChange.run", return_value=root)

    requirement = "New requirement"
    prd_filename = "prd.md"
    design_filename = "design.md"
    task_filename = "task.md"
    code_plan_and_change_context = CodePlanAndChangeContext(
        requirement=requirement,
        prd_filename=prd_filename,
        design_filename=design_filename,
        task_filename=task_filename,
    )
    node = await WriteCodePlanAndChange(i_context=code_plan_and_change_context).run()

    assert "Code Plan And Change" in node.instruct_content.model_dump()


@pytest.mark.asyncio
async def test_refine_code(mocker):
    mocker.patch.object(WriteCode, "_aask", return_value=REFINED_CODE_SAMPLE)
    prompt = REFINED_TEMPLATE.format(
        user_requirement=NEW_REQUIREMENT_SAMPLE,
        code_plan_and_change=CODE_PLAN_AND_CHANGE_SAMPLE,
        design=DESIGN_SAMPLE,
        task=TASKS_SAMPLE,
        code=REFINED_CODE_INPUT_SAMPLE,
        logs="",
        feedback="",
        filename="game.py",
        summary_log="",
    )
    code = await WriteCode().write_code(prompt=prompt)
    assert "def" in code
