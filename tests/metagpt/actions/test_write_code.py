#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_code.py
@Modifiled By: mashenquan, 2023-12-6. According to RFC 135
"""
import pytest
from metagpt.provider.openai_api import OpenAIGPTAPI as LLM
from metagpt.actions.write_code import WriteCode
from metagpt.logs import logger
from metagpt.schema import CodingContext, Document
from tests.metagpt.actions.mock import TASKS_2, WRITE_CODE_PROMPT_SAMPLE


@pytest.mark.asyncio
async def test_write_code():
    context = CodingContext(
        filename="task_filename.py", design_doc=Document(content="设计一个名为'add'的函数，该函数接受两个整数作为输入，并返回它们的和。")
    )
    doc = Document(content=context.json())
    write_code = WriteCode(context=doc)

    code = await write_code.run()
    logger.info(code.json())

    # 我们不能精确地预测生成的代码，但我们可以检查某些关键字
    assert "def add" in code.code_doc.content
    assert "return" in code.code_doc.content


@pytest.mark.asyncio
async def test_write_code_directly():
    prompt = WRITE_CODE_PROMPT_SAMPLE + "\n" + TASKS_2[0]
    llm = LLM()
    rsp = await llm.aask(prompt)
    logger.info(rsp)
