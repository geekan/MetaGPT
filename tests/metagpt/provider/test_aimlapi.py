#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : test_aimlapi.py
@Desc    : aimlapi.com registration, request params and attribution headers.
"""
import re

import pytest

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.aimlapi import (
    AIMLAPI_ATTRIBUTION_HEADERS,
    AIMLAPI_BASE_URL,
    AIMLAPI_DISPLAY_NAME,
    aimlapi_default_headers,
    is_aimlapi,
)
from metagpt.provider.llm_provider_registry import LLM_REGISTRY
from metagpt.provider.openai_api import OpenAILLM

# apps/api gateway contract; a malformed id is dropped silently and earns nothing
PARTNER_ID_PATTERN = re.compile(r"^part_[A-Za-z0-9]{1,64}$")

SOURCE_PATTERN = re.compile(r"^(web|agent|mcp)/[a-z0-9-]{1,32}$")


def aimlapi_config(**kwargs) -> LLMConfig:
    params = {
        "api_type": LLMType.AIMLAPI,
        "base_url": AIMLAPI_BASE_URL,
        "api_key": "mock_api_key",
        "model": "openai/gpt-5-5",
    }
    params.update(kwargs)
    return LLMConfig(**params)


def test_api_type_is_registered_to_openai_provider():
    assert LLMType("aimlapi") is LLMType.AIMLAPI
    assert LLM_REGISTRY.get_provider(LLMType.AIMLAPI) is OpenAILLM


def test_display_name():
    assert AIMLAPI_DISPLAY_NAME == "aimlapi.com"


def test_partner_id_is_well_formed():
    """A malformed partner id is accepted by the gateway and then ignored, so the
    only place a typo can be caught is here."""
    assert PARTNER_ID_PATTERN.match(AIMLAPI_ATTRIBUTION_HEADERS["X-AIMLAPI-Partner-ID"])


def test_source_is_well_formed():
    assert SOURCE_PATTERN.match(AIMLAPI_ATTRIBUTION_HEADERS["X-AIMLAPI-Source"])


def test_referer_and_title_point_at_the_calling_app():
    """`HTTP-Referer` / `X-Title` identify MetaGPT, not the provider."""
    assert "MetaGPT" in AIMLAPI_ATTRIBUTION_HEADERS["HTTP-Referer"]
    assert AIMLAPI_ATTRIBUTION_HEADERS["X-Title"] == "MetaGPT"


def test_client_kwargs_carry_attribution():
    kwargs = OpenAILLM(aimlapi_config())._make_client_kwargs()
    for key, value in AIMLAPI_ATTRIBUTION_HEADERS.items():
        assert kwargs["default_headers"][key] == value


@pytest.mark.parametrize("api_type", [LLMType.OPENAI, LLMType.OPENROUTER, LLMType.DEEPSEEK])
def test_no_attribution_for_other_providers(api_type):
    """Attribution must never ride along to somebody else's API."""
    config = aimlapi_config(api_type=api_type, base_url="https://api.openai.com/v1")
    assert "default_headers" not in OpenAILLM(config)._make_client_kwargs()
    assert aimlapi_default_headers(config) == {}


def test_no_attribution_for_a_proxy_fronting_us():
    """`api_type: aimlapi` pointed at a third-party proxy is still a third party."""
    config = aimlapi_config(base_url="https://proxy.example.com/aimlapi/v1")
    assert not is_aimlapi(config)
    assert "default_headers" not in OpenAILLM(config)._make_client_kwargs()


def test_headers_are_merged_not_assigned():
    """A caller's own header wins, and the shared constant is never mutated."""
    before = dict(AIMLAPI_ATTRIBUTION_HEADERS)
    merged = aimlapi_default_headers(aimlapi_config(), {"X-Title": "custom", "X-Extra": "kept"})

    assert merged["X-Title"] == "custom"
    assert merged["X-Extra"] == "kept"
    assert merged["X-AIMLAPI-Partner-ID"] == AIMLAPI_ATTRIBUTION_HEADERS["X-AIMLAPI-Partner-ID"]
    assert merged is not AIMLAPI_ATTRIBUTION_HEADERS
    assert AIMLAPI_ATTRIBUTION_HEADERS == before


def test_request_params_omit_unset_keys():
    """aimlapi.com rejects `null` on `tools`, `seed`, `response_format` and others
    with a 400 on the stricter models, so unset options must be absent from the
    body rather than sent as null. `tools: null` is the one that matters: it
    succeeds on turn 1 of an agent loop and fails on turn 2."""
    llm = OpenAILLM(aimlapi_config())
    kwargs = llm._cons_kwargs([{"role": "user", "content": "hi"}])

    assert None not in kwargs.values()
    for key in ("tools", "tool_choice", "seed", "response_format", "parallel_tool_calls", "stop"):
        assert key not in kwargs
