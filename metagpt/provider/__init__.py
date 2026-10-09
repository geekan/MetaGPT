#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 22:59
@Author  : alexanderwu
@File    : __init__.py
"""

from metagpt.logs import logger

_optional_import_errors = []


def _optional(import_fn, name):
    try:
        return import_fn()
    except Exception as e:  # optional heavy/SDK deps may be missing in slim envs
        _optional_import_errors.append(f"{name}: {e}")
        logger.warning(f"[provider] optional import skipped for {name}: {e}")
        return None


GeminiLLM = _optional(lambda: __import__("metagpt.provider.google_gemini_api", fromlist=["GeminiLLM"]).GeminiLLM, "GeminiLLM")
OllamaLLM = _optional(lambda: __import__("metagpt.provider.ollama_api", fromlist=["OllamaLLM"]).OllamaLLM, "OllamaLLM")
OpenAILLM = _optional(lambda: __import__("metagpt.provider.openai_api", fromlist=["OpenAILLM"]).OpenAILLM, "OpenAILLM")
ZhiPuAILLM = _optional(lambda: __import__("metagpt.provider.zhipuai_api", fromlist=["ZhiPuAILLM"]).ZhiPuAILLM, "ZhiPuAILLM")
AzureOpenAILLM = _optional(
    lambda: __import__("metagpt.provider.azure_openai_api", fromlist=["AzureOpenAILLM"]).AzureOpenAILLM, "AzureOpenAILLM"
)
MetaGPTLLM = _optional(lambda: __import__("metagpt.provider.metagpt_api", fromlist=["MetaGPTLLM"]).MetaGPTLLM, "MetaGPTLLM")
HumanProvider = _optional(
    lambda: __import__("metagpt.provider.human_provider", fromlist=["HumanProvider"]).HumanProvider, "HumanProvider"
)
SparkLLM = _optional(lambda: __import__("metagpt.provider.spark_api", fromlist=["SparkLLM"]).SparkLLM, "SparkLLM")
QianFanLLM = _optional(lambda: __import__("metagpt.provider.qianfan_api", fromlist=["QianFanLLM"]).QianFanLLM, "QianFanLLM")
DashScopeLLM = _optional(
    lambda: __import__("metagpt.provider.dashscope_api", fromlist=["DashScopeLLM"]).DashScopeLLM, "DashScopeLLM"
)
AnthropicLLM = _optional(
    lambda: __import__("metagpt.provider.anthropic_api", fromlist=["AnthropicLLM"]).AnthropicLLM, "AnthropicLLM"
)
BedrockLLM = _optional(lambda: __import__("metagpt.provider.bedrock_api", fromlist=["BedrockLLM"]).BedrockLLM, "BedrockLLM")
ArkLLM = _optional(lambda: __import__("metagpt.provider.ark_api", fromlist=["ArkLLM"]).ArkLLM, "ArkLLM")
OpenrouterReasoningLLM = _optional(
    lambda: __import__("metagpt.provider.openrouter_reasoning", fromlist=["OpenrouterReasoningLLM"]).OpenrouterReasoningLLM,
    "OpenrouterReasoningLLM",
)

from metagpt.provider.circuit_breaker import (  # noqa: E402
    CircuitBreaker,
    CircuitOpenError,
    assert_allowed,
    circuit_breaker_status,
    get_circuit_breaker,
    reset_circuit_breaker,
    should_allow_request,
)
from metagpt.provider.fallback_router import FallbackLLM  # noqa: E402
from metagpt.provider.task_chains import (  # noqa: E402
    DEFAULT_TASK_CHAINS,
    build_provider_chain,
    build_task_chain,
    is_provider_configured,
)

from metagpt.provider.rate_limiter import RateLimiter, RateLimitConfig, get_rate_limiter  # noqa: E402
from metagpt.provider.retry_policy import DEFAULT_RETRY_POLICY, RetryPolicy, with_retry  # noqa: E402
from metagpt.provider.token_usage import TokenUsageTracker, get_token_usage_tracker, normalize_usage  # noqa: E402
from metagpt.provider.streaming import StreamAccumulator, create_stream_collector, estimate_tokens  # noqa: E402
from metagpt.provider.context_manager import ContextManager, get_context_manager  # noqa: E402
from metagpt.provider.tool_calling import (  # noqa: E402
    ToolRegistry,
    parse_tool_calls,
    to_openai_tool,
    to_openai_tools,
)

__all__ = [
    "GeminiLLM",
    "OpenAILLM",
    "ZhiPuAILLM",
    "AzureOpenAILLM",
    "MetaGPTLLM",
    "OllamaLLM",
    "HumanProvider",
    "SparkLLM",
    "QianFanLLM",
    "DashScopeLLM",
    "AnthropicLLM",
    "BedrockLLM",
    "ArkLLM",
    "OpenrouterReasoningLLM",
    "CircuitBreaker",
    "CircuitOpenError",
    "FallbackLLM",
    "build_task_chain",
    "build_provider_chain",
    "is_provider_configured",
    "DEFAULT_TASK_CHAINS",
    "get_circuit_breaker",
    "reset_circuit_breaker",
    "circuit_breaker_status",
    "should_allow_request",
    "assert_allowed",
    "RetryPolicy",
    "DEFAULT_RETRY_POLICY",
    "with_retry",
    "RateLimiter",
    "RateLimitConfig",
    "get_rate_limiter",
    "TokenUsageTracker",
    "get_token_usage_tracker",
    "normalize_usage",
    "StreamAccumulator",
    "create_stream_collector",
    "estimate_tokens",
    "ContextManager",
    "get_context_manager",
    "ToolRegistry",
    "to_openai_tool",
    "to_openai_tools",
    "parse_tool_calls",
]
