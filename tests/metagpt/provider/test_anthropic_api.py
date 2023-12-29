#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of Claude2


import pytest
from anthropic.resources.completions import Completion

from metagpt.config import CONFIG
from metagpt.provider.anthropic_api import Claude2

CONFIG.anthropic_api_key = "xxx"

prompt = "who are you"
resp = "I'am Claude2"


def mock_anthropic_completions_create(self, model: str, prompt: str, max_tokens_to_sample: int) -> Completion:
    return Completion(id="xx", completion=resp, model="claude-2", stop_reason="stop_sequence", type="completion")


async def mock_anthropic_acompletions_create(self, model: str, prompt: str, max_tokens_to_sample: int) -> Completion:
    return Completion(id="xx", completion=resp, model="claude-2", stop_reason="stop_sequence", type="completion")


def test_claude2_ask(mocker):
    mocker.patch("anthropic.resources.completions.Completions.create", mock_anthropic_completions_create)
    assert resp == Claude2().ask(prompt)


@pytest.mark.asyncio
async def test_claude2_aask(mocker):
    mocker.patch("anthropic.resources.completions.AsyncCompletions.create", mock_anthropic_acompletions_create)
    assert resp == await Claude2().aask(prompt)
