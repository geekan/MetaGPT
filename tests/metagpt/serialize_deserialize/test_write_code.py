# -*- coding: utf-8 -*-
# @Date    : 11/23/2023 10:56 AM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

import pytest

from metagpt.actions import WriteCode
from metagpt.schema import CodingContext, Document


def test_write_design_serdeser(context):
    action = WriteCode(context=context)
    ser_action_dict = action.model_dump()
    assert ser_action_dict["name"] == "WriteCode"
    assert "llm" not in ser_action_dict  # not export


@pytest.mark.asyncio
async def test_write_code_serdeser(context):
    context.src_workspace = context.repo.workdir / "srcs"
    coding_context = CodingContext(
        filename="test_code.py", design_doc=Document(content="write add function to calculate two numbers")
    )
    doc = Document(content=coding_context.model_dump_json())
    action = WriteCode(i_context=doc, context=context)
    serialized_data = action.model_dump()
    new_action = WriteCode(**serialized_data, context=context)

    assert new_action.name == "WriteCode"
    await action.run()
