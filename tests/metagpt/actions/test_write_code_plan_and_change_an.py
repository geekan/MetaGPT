#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_write_code_plan_and_change_an.py
"""
import json

import pytest
from openai._models import BaseModel

from metagpt.actions.action_node import ActionNode
from metagpt.actions.write_code import WriteCode
from metagpt.actions.write_code_plan_and_change_an import (
    REFINED_TEMPLATE,
    WriteCodePlanAndChange,
)
from metagpt.logs import logger
from metagpt.schema import CodePlanAndChangeContext
from metagpt.utils.common import CodeParser
from tests.data.incremental_dev_project.mock import (
    CODE_PLAN_AND_CHANGE_SAMPLE,
    DESIGN_SAMPLE,
    NEW_REQUIREMENT_SAMPLE,
    REFINED_CODE_INPUT_SAMPLE,
    REFINED_CODE_SAMPLE,
    REFINED_DESIGN_JSON,
    REFINED_PRD_JSON,
    REFINED_TASK_JSON,
    TASK_SAMPLE,
)
from tests.metagpt.actions.test_write_code import setup_inc_workdir


def mock_code_plan_and_change():
    return CODE_PLAN_AND_CHANGE_SAMPLE


@pytest.mark.asyncio
async def test_write_code_plan_and_change_an(mocker, context, git_dir):
    context = setup_inc_workdir(context, inc=True)
    await context.repo.docs.prd.save(filename="2.json", content=json.dumps(REFINED_PRD_JSON))
    await context.repo.docs.system_design.save(filename="2.json", content=json.dumps(REFINED_DESIGN_JSON))
    await context.repo.docs.task.save(filename="2.json", content=json.dumps(REFINED_TASK_JSON))

    await context.repo.with_src_path(context.repo.old_workspace).srcs.save(
        filename="game.py", content=CodeParser.parse_code(block="", text=REFINED_CODE_INPUT_SAMPLE)
    )

    root = ActionNode.from_children(
        "WriteCodePlanAndChange", [ActionNode(key="", expected_type=str, instruction="", example="")]
    )
    root.instruct_content = BaseModel()
    root.instruct_content.model_dump = mock_code_plan_and_change
    mocker.patch(
        "metagpt.actions.write_code_plan_and_change_an.WRITE_CODE_PLAN_AND_CHANGE_NODE.fill", return_value=root
    )

    code_plan_and_change_context = CodePlanAndChangeContext(
        requirement="New requirement",
        prd_filename="2.json",
        design_filename="2.json",
        task_filename="2.json",
    )
    node = await WriteCodePlanAndChange(i_context=code_plan_and_change_context, context=context).run()

    assert "Development Plan" in node.instruct_content.model_dump()
    assert "Incremental Change" in node.instruct_content.model_dump()


@pytest.mark.asyncio
async def test_refine_code(mocker):
    mocker.patch.object(WriteCode, "_aask", return_value=REFINED_CODE_SAMPLE)
    prompt = REFINED_TEMPLATE.format(
        user_requirement=NEW_REQUIREMENT_SAMPLE,
        code_plan_and_change=CODE_PLAN_AND_CHANGE_SAMPLE,
        design=DESIGN_SAMPLE,
        task=TASK_SAMPLE,
        code=REFINED_CODE_INPUT_SAMPLE,
        logs="",
        feedback="",
        filename="game.py",
        summary_log="",
    )
    code = await WriteCode().write_code(prompt=prompt)
    assert "def" in code


@pytest.mark.asyncio
async def test_get_old_code(context, git_dir):
    context = setup_inc_workdir(context, inc=True)
    await context.repo.with_src_path(context.repo.old_workspace).srcs.save(
        filename="game.py", content=REFINED_CODE_INPUT_SAMPLE
    )

    code_plan_and_change_context = CodePlanAndChangeContext(
        requirement="New requirement",
        prd_filename="1.json",
        design_filename="1.json",
        task_filename="1.json",
    )
    action = WriteCodePlanAndChange(context=context, i_context=code_plan_and_change_context)

    old_codes = await action.get_old_codes()
    logger.info(old_codes)

    assert "def" in old_codes
    assert "class" in old_codes
