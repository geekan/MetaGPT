#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of HumanProvider

import pytest

from metagpt.provider.human_provider import HumanProvider

resp_content = "test"


def mock_llm_ask(msg: str, timeout: int = 3) -> str:
    return resp_content


async def mock_llm_aask(msg: str, timeout: int = 3) -> str:
    return mock_llm_ask(msg)


def test_human_provider(mocker):
    mocker.patch("metagpt.provider.human_provider.HumanProvider.ask", mock_llm_ask)
    human_provider = HumanProvider()

    assert resp_content == human_provider.ask(None)

    assert not human_provider.completion(messages=[])


@pytest.mark.asyncio
async def test_async_human_provider(mocker):
    mocker.patch("metagpt.provider.human_provider.HumanProvider.aask", mock_llm_aask)
    human_provider = HumanProvider()

    resp = await human_provider.aask(None)
    assert resp_content == resp

    resp = await human_provider.acompletion([])
    assert not resp
