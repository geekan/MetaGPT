#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of HumanProvider

import pytest

from metagpt.provider.human_provider import HumanProvider
from tests.metagpt.provider.mock_llm_config import mock_llm_config

resp_content = "test"
resp_exit = "exit"


@pytest.mark.asyncio
async def test_async_human_provider(mocker):
    mocker.patch("builtins.input", lambda _: resp_content)
    human_provider = HumanProvider(mock_llm_config)

    resp = human_provider.ask(resp_content)
    assert resp == resp_content
    resp = await human_provider.aask(None)
    assert resp_content == resp

    mocker.patch("builtins.input", lambda _: resp_exit)
    with pytest.raises(SystemExit):
        human_provider.ask(resp_exit)

    resp = await human_provider.acompletion([])
    assert not resp

    resp = await human_provider.acompletion_text([])
    assert resp == ""
