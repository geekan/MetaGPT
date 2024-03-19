#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of ollama api

import json
from typing import Any, Tuple

import pytest

from metagpt.provider.ollama_api import OllamaLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config
from tests.metagpt.provider.req_resp_const import (
    llm_general_chat_funcs_test,
    messages,
    prompt,
    resp_cont_tmpl,
)

resp_cont = resp_cont_tmpl.format(name="ollama")
default_resp = {"message": {"role": "assistant", "content": resp_cont}}


async def mock_ollama_arequest(self, stream: bool = False, **kwargs) -> Tuple[Any, Any, bool]:
    if stream:

        class Iterator(object):
            events = [
                b'{"message": {"role": "assistant", "content": "I\'m ollama"}, "done": false}',
                b'{"prompt_eval_count": 20, "eval_count": 20, "done": true}',
            ]

            async def __aiter__(self):
                for event in self.events:
                    yield event

        return Iterator(), None, None
    else:
        raw_default_resp = default_resp.copy()
        raw_default_resp.update({"prompt_eval_count": 20, "eval_count": 20})
        return json.dumps(raw_default_resp).encode(), None, None


@pytest.mark.asyncio
async def test_gemini_acompletion(mocker):
    mocker.patch("metagpt.provider.general_api_requestor.GeneralAPIRequestor.arequest", mock_ollama_arequest)

    ollama_llm = OllamaLLM(mock_llm_config)

    resp = await ollama_llm.acompletion(messages)
    assert resp["message"]["content"] == default_resp["message"]["content"]

    resp = await ollama_llm.aask(prompt, stream=False)
    assert resp == resp_cont

    await llm_general_chat_funcs_test(ollama_llm, prompt, messages, resp_cont)
