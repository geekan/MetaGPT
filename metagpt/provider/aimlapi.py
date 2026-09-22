#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : aimlapi.py
@Desc    : Constants and attribution headers for aimlapi.com.

aimlapi.com speaks the OpenAI chat-completions wire format, so it is served by
``OpenAILLM`` rather than by a provider class of its own. The only thing it needs
beyond registration is the attribution block below, which tells the gateway that
the request came from MetaGPT.

The headers are deliberately gated on both ``api_type`` *and* the request host:
attribution that rides along to a different provider — or to a proxy that merely
fronts the same API — is wrong, and gating on the configured provider alone does
not prevent that.
"""
from typing import Optional
from urllib.parse import urlparse

from metagpt.configs.llm_config import LLMConfig, LLMType

# Human-readable name of the service, for anywhere a label is shown to a user.
AIMLAPI_DISPLAY_NAME = "aimlapi.com"

AIMLAPI_BASE_URL = "https://api.aimlapi.com/v1"

# Hosts the attribution headers may be sent to. Anything else, including a proxy
# in front of aimlapi.com, gets no headers.
AIMLAPI_HOSTS = frozenset({"api.aimlapi.com"})

# `HTTP-Referer` / `X-Title` follow the OpenRouter convention and identify the
# *calling* application, i.e. MetaGPT, not the provider.
AIMLAPI_ATTRIBUTION_HEADERS = {
    "HTTP-Referer": "https://github.com/FoundationAgents/MetaGPT",
    "X-Title": "MetaGPT",
    "X-AIMLAPI-Partner-ID": "part_ae9uKiFKtDmVG2KCkYwhrdQs",
    "X-AIMLAPI-Source": "agent/metagpt",
}


def is_aimlapi(config: LLMConfig) -> bool:
    """True when `config` targets aimlapi.com itself."""
    if config.api_type != LLMType.AIMLAPI:
        return False
    host = (urlparse(config.base_url or "").hostname or "").lower()
    return host in AIMLAPI_HOSTS


def aimlapi_default_headers(config: LLMConfig, headers: Optional[dict] = None) -> dict:
    """Return the headers to send for `config`, as a new dict.

    Values already present in `headers` win, so a caller's own configuration is
    never silently dropped, and ``AIMLAPI_ATTRIBUTION_HEADERS`` is never mutated.
    """
    if not is_aimlapi(config):
        return dict(headers or {})
    return {**AIMLAPI_ATTRIBUTION_HEADERS, **(headers or {})}
