#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of Claude2

import pytest
from anthropic.resources.completions import Completion

from metagpt.provider.anthropic_api import AnthropicLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_anthropic
from tests.metagpt.provider.req_resp_const import (
    get_anthropic_response,
    llm_general_chat_funcs_test,
    messages,
    prompt,
    resp_cont_tmpl,
)

name = "claude-3-opus-20240229"
resp_cont = resp_cont_tmpl.format(name=name)


async def mock_anthropic_messages_create(
    self, messages: list[dict], model: str, stream: bool = True, max_tokens: int = None, system: str = None
) -> Completion:
    if stream:

        async def aresp_iterator():
            resps = get_anthropic_response(name, stream=True)
            for resp in resps:
                yield resp

        return aresp_iterator()
    else:
        return get_anthropic_response(name)


@pytest.mark.asyncio
async def test_anthropic_acompletion(mocker):
    mocker.patch("anthropic.resources.messages.AsyncMessages.create", mock_anthropic_messages_create)

    anthropic_llm = AnthropicLLM(mock_llm_config_anthropic)

    resp = await anthropic_llm.acompletion(messages)
    assert resp.content[0].text == resp_cont

    await llm_general_chat_funcs_test(anthropic_llm, prompt, messages, resp_cont)
