#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/03
@Author  : mannaandpoem
@File    : test_write_code_guideline_an.py
"""
import pytest

from metagpt.actions.action_node import ActionNode
from metagpt.actions.write_code import WriteCode
from metagpt.actions.write_code_guideline_an import (
    CODE_GUIDELINE_CONTEXT,
    REFINED_CODE_TEMPLATE,
    WriteCodeGuideline,
)
from tests.data.incremental_dev_project.mock import (
    DESIGN_SAMPLE,
    GUIDELINES_AND_INCREMENTAL_CHANGE_SAMPLE,
    NEW_REQUIREMENT_SAMPLE,
    OLD_CODE_SAMPLE,
    REFINED_CODE_INPUT_SAMPLE,
    REFINED_CODE_SAMPLE,
    REFINED_DESIGN_JSON,
    REFINED_PRD_JSON,
    REFINED_TASKS_JSON,
    TASKS_SAMPLE,
)


@pytest.mark.asyncio
async def test_write_code_guideline_an(mocker):
    root = ActionNode.from_children(
        "WriteCodeGuideline", [ActionNode(key="", expected_type=str, instruction="", example="")]
    )
    root.instruct_content = GUIDELINES_AND_INCREMENTAL_CHANGE_SAMPLE
    mocker.patch("metagpt.actions.write_code_guideline_an.WriteCodeGuideline.run", return_value=root)

    write_code_guideline = WriteCodeGuideline()
    context = CODE_GUIDELINE_CONTEXT.format(
        user_requirement=NEW_REQUIREMENT_SAMPLE,
        product_requirement_pools=REFINED_PRD_JSON.get("Refined Requirement Pool", ""),
        design=REFINED_DESIGN_JSON,
        tasks=REFINED_TASKS_JSON,
        code=OLD_CODE_SAMPLE,
    )
    node = await write_code_guideline.run(context=context)
    assert "Guidelines and Incremental Change" in node.instruct_content


@pytest.mark.asyncio
async def test_refine_code(mocker):
    mocker.patch("metagpt.actions.write_code.WriteCode.write_code", return_value=REFINED_CODE_SAMPLE)
    prompt = REFINED_CODE_TEMPLATE.format(
        user_requirement=NEW_REQUIREMENT_SAMPLE,
        guideline=GUIDELINES_AND_INCREMENTAL_CHANGE_SAMPLE,
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
