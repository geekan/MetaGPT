#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of Claude2


import pytest
from anthropic.resources.completions import Completion

from metagpt.provider.anthropic_api import Claude2
from tests.metagpt.provider.mock_llm_config import mock_llm_config
from tests.metagpt.provider.req_resp_const import prompt, resp_cont_tmpl

resp_cont = resp_cont_tmpl.format(name="Claude")


def mock_anthropic_completions_create(self, model: str, prompt: str, max_tokens_to_sample: int) -> Completion:
    return Completion(id="xx", completion=resp_cont, model="claude-2", stop_reason="stop_sequence", type="completion")


async def mock_anthropic_acompletions_create(self, model: str, prompt: str, max_tokens_to_sample: int) -> Completion:
    return Completion(id="xx", completion=resp_cont, model="claude-2", stop_reason="stop_sequence", type="completion")


def test_claude2_ask(mocker):
    mocker.patch("anthropic.resources.completions.Completions.create", mock_anthropic_completions_create)
    assert resp_cont == Claude2(mock_llm_config).ask(prompt)


@pytest.mark.asyncio
async def test_claude2_aask(mocker):
    mocker.patch("anthropic.resources.completions.AsyncCompletions.create", mock_anthropic_acompletions_create)
    assert resp_cont == await Claude2(mock_llm_config).aask(prompt)
