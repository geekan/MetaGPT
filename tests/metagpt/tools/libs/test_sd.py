# -*- coding: utf-8 -*-
# @Date    : 1/10/2024 10:07 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.tools.libs.sd_engine import SDEngine


def test_sd_tools():
    engine = SDEngine()
    prompt = "1boy,  hansom"
    engine.construct_payload(prompt)
    engine.simple_run_t2i(engine.payload)


def test_sd_construct_payload():
    engine = SDEngine()
    prompt = "1boy,  hansom"
    engine.construct_payload(prompt)
    assert "negative_prompt" in engine.payload


@pytest.mark.asyncio
async def test_sd_asyn_t2i():
    engine = SDEngine()
    prompt = "1boy,  hansom"
    engine.construct_payload(prompt)
    await engine.run_t2i([engine.payload])
    assert "negative_prompt" in engine.payload
