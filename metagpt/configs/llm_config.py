#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 16:33
@Author  : alexanderwu
@File    : llm_config.py
"""

from enum import Enum
from typing import Optional

from pydantic import field_validator

from metagpt.configs.compress_msg_config import CompressType
from metagpt.const import CONFIG_ROOT, LLM_API_TIMEOUT, METAGPT_ROOT
from metagpt.utils.yaml_model import YamlModel


class LLMType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CLAUDE = "claude"  # alias name of anthropic
    SPARK = "spark"
    ZHIPUAI = "zhipuai"
    FIREWORKS = "fireworks"
    OPEN_LLM = "open_llm"
    GEMINI = "gemini"
    METAGPT = "metagpt"
    AZURE = "azure"
    OLLAMA = "ollama"  # /chat at ollama api
    OLLAMA_GENERATE = "ollama.generate"  # /generate at ollama api
    OLLAMA_EMBEDDINGS = "ollama.embeddings"  # /embeddings at ollama api
    OLLAMA_EMBED = "ollama.embed"  # /embed at ollama api
    QIANFAN = "qianfan"  # Baidu BCE
    DASHSCOPE = "dashscope"  # Aliyun LingJi DashScope
    MOONSHOT = "moonshot"
    MISTRAL = "mistral"
    YI = "yi"  # lingyiwanwu
    OPEN_ROUTER = "open_router"
    DEEPSEEK = "deepseek"
    SILICONFLOW = "siliconflow"
    OPENROUTER = "openrouter"
    OPENROUTER_REASONING = "openrouter_reasoning"
    BEDROCK = "bedrock"
    ARK = "ark"  # https://www.volcengine.com/docs/82379/1263482#python-sdk
    UNIFY = "unify"

    def __missing__(self, key):
        return self.OPENAI


class LLMConfig(YamlModel):
    """Config for LLM

    OpenAI: https://github.com/openai/openai-python/blob/main/src/openai/resources/chat/completions.py#L681
    Optional Fields in pydantic: https://docs.pydantic.dev/latest/migration/#required-optional-and-nullable-fields
    """

    api_key: str = "sk-"
    api_type: LLMType = LLMType.OPENAI
    base_url: str = "https://api.openai.com/v1"
    api_version: Optional[str] = None

    model: Optional[str] = None  # also stands for DEPLOYMENT_NAME
    pricing_plan: Optional[str] = None  # Cost Settlement Plan Parameters.

    # For Cloud Service Provider like Baidu/ Alibaba
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    session_token: Optional[str] = None
    endpoint: Optional[str] = None  # for self-deployed model on the cloud

    # For Spark(Xunfei), maybe remove later
    app_id: Optional[str] = None
    api_secret: Optional[str] = None
    domain: Optional[str] = None

    # For Chat Completion
    max_token: int = 4096
    temperature: float = 0.0
    top_p: float = 1.0
    top_k: int = 0
    repetition_penalty: float = 1.0
    stop: Optional[str] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    best_of: Optional[int] = None
    n: Optional[int] = None
    stream: bool = True
    seed: Optional[int] = None
    # https://cookbook.openai.com/examples/using_logprobs
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None
    timeout: int = 600
    context_length: Optional[int] = None  # Max input tokens

    # For Amazon Bedrock
    region_name: str = None

    # For Network
    proxy: Optional[str] = None

    # Cost Control
    calc_usage: bool = True

    # Compress request messages under token limit
    compress_type: CompressType = CompressType.NO_COMPRESS

    # For Messages Control
    use_system_prompt: bool = True

    # reasoning / thinking switch
    reasoning: bool = False
    reasoning_max_token: int = 4000  # reasoning budget tokens to generate, usually smaller than max_token

    @field_validator("api_key")
    @classmethod
    def check_llm_key(cls, v):
        if v in ["", None, "YOUR_API_KEY"]:
            repo_config_path = METAGPT_ROOT / "config/config2.yaml"
            root_config_path = CONFIG_ROOT / "config2.yaml"
            if root_config_path.exists():
                raise ValueError(
                    f"Please set your API key in {root_config_path}. If you also set your config in {repo_config_path}, \n"
                    f"the former will overwrite the latter. This may cause unexpected result.\n"
                )
            elif repo_config_path.exists():
                raise ValueError(f"Please set your API key in {repo_config_path}")
            else:
                raise ValueError("Please set your API key in config2.yaml")
        return v

    @field_validator("timeout")
    @classmethod
    def check_timeout(cls, v):
        return v or LLM_API_TIMEOUT
