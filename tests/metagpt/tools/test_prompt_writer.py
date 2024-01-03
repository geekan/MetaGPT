#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/2 17:46
@Author  : alexanderwu
@File    : test_prompt_writer.py
"""

import pytest

from metagpt.logs import logger
from metagpt.tools.prompt_writer import (
    BEAGECTemplate,
    EnronTemplate,
    GPTPromptGenerator,
    WikiHowTemplate,
)


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_api")
async def test_gpt_prompt_generator(llm_api):
    generator = GPTPromptGenerator()
    example = (
        "商品名称:WonderLab 新肌果味代餐奶昔 小胖瓶 胶原蛋白升级版 饱腹代餐粉6瓶 75g/瓶(6瓶/盒) 店铺名称:金力宁食品专营店 " "品牌:WonderLab 保质期:1年 产地:中国 净含量:450g"
    )

    results = await llm_api.aask_batch(generator.gen(example))
    logger.info(results)
    assert len(results) > 0


@pytest.mark.usefixtures("llm_api")
def test_wikihow_template(llm_api):
    template = WikiHowTemplate()
    question = "learn Python"
    step = 5

    results = template.gen(question, step)
    assert len(results) > 0
    assert any("Give me 5 steps to learn Python." in r for r in results)


@pytest.mark.usefixtures("llm_api")
def test_enron_template(llm_api):
    template = EnronTemplate()
    subj = "Meeting Agenda"

    results = template.gen(subj)
    assert len(results) > 0
    assert any('Write an email with the subject "Meeting Agenda".' in r for r in results)


def test_beagec_template():
    template = BEAGECTemplate()

    results = template.gen()
    assert len(results) > 0
    assert any(
        "Edit and revise this document to improve its grammar, vocabulary, spelling, and style." in r for r in results
    )


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
