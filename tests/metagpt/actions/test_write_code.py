#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_code.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation.
"""
import pytest

from metagpt.config import Config
from metagpt.provider.openai_api import OpenAIGPTAPI as LLM, CostManager
from metagpt.actions.write_code import WriteCode
from metagpt.logs import logger
from tests.metagpt.actions.mock import TASKS_2, WRITE_CODE_PROMPT_SAMPLE


@pytest.mark.asyncio
async def test_write_code():
    api_design = "设计一个名为'add'的函数，该函数接受两个整数作为输入，并返回它们的和。"
    conf = Config()
    cost_manager = CostManager(**conf.runtime_options)
    llm = LLM(options=conf.runtime_options, cost_manager=cost_manager)
    write_code = WriteCode(options=conf.runtime_options, name="write_code", llm=llm)

    code = await write_code.run(api_design, "filename")
    logger.info(code)

    # 我们不能精确地预测生成的代码，但我们可以检查某些关键字
    assert 'def add' in code
    assert 'return' in code


@pytest.mark.asyncio
async def test_write_code_directly():
    prompt = WRITE_CODE_PROMPT_SAMPLE + '\n' + TASKS_2[0]
    options = Config().runtime_options
    llm = LLM(options=options, cost_manager=CostManager(**options))
    rsp = await llm.aask(prompt)
    logger.info(rsp)
