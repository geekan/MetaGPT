#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of Claude2

import pytest

from metagpt.provider.anthropic_api import Claude2

prompt = "who are you"
resp = "I'am Claude2"


def mock_llm_ask(self, msg: str) -> str:
    return resp


async def mock_llm_aask(self, msg: str) -> str:
    return resp


def test_claude2_ask(mocker):
    mocker.patch("metagpt.provider.anthropic_api.Claude2.ask", mock_llm_ask)
    assert resp == Claude2().ask(prompt)


@pytest.mark.asyncio
async def test_claude2_aask(mocker):
    mocker.patch("metagpt.provider.anthropic_api.Claude2.aask", mock_llm_aask)
    assert resp == await Claude2().aask(prompt)
