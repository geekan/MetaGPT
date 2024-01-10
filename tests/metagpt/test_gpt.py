#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 19:47
@Author  : alexanderwu
@File    : test_gpt.py
"""
import openai
import pytest

from metagpt.config import CONFIG
from metagpt.logs import logger


@pytest.mark.usefixtures("llm_api")
class TestGPT:
    @pytest.mark.asyncio
    async def test_llm_api_aask(self, llm_api):
        answer = await llm_api.aask("hello chatgpt", stream=False)
        logger.info(answer)
        assert len(answer) > 0

        answer = await llm_api.aask("hello chatgpt", stream=True)
        logger.info(answer)
        assert len(answer) > 0

    @pytest.mark.asyncio
    async def test_llm_api_aask_code(self, llm_api):
        try:
            answer = await llm_api.aask_code(["请扮演一个Google Python专家工程师，如果理解，回复明白", "写一个hello world"], timeout=60)
            logger.info(answer)
            assert len(answer) > 0
        except openai.BadRequestError:
            assert CONFIG.OPENAI_API_TYPE == "azure"

    @pytest.mark.asyncio
    async def test_llm_api_costs(self, llm_api):
        await llm_api.aask("hello chatgpt", stream=False)
        costs = llm_api.get_costs()
        logger.info(costs)
        assert costs.total_cost > 0


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
