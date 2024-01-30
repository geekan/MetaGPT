#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/4 16:33
# @Author  : alexanderwu
# @File    : llm_config.py

from enum import Enum
from typing import Optional

from pydantic import field_validator

from metagpt.utils.yaml_model import YamlModel


class LLMType(Enum):
    """Defines the types of Language Learning Models (LLM) supported.

    Attributes:
        OPENAI: Represents the OpenAI's models.
        ANTHROPIC: Represents the Anthropic's models.
        SPARK: Represents the Spark's models.
        ZHIPUAI: Represents the ZhipuAI's models.
        FIREWORKS: Represents the Fireworks' models.
        OPEN_LLM: Represents other open-source LLMs.
        GEMINI: Represents the Gemini's models.
        METAGPT: Represents the MetaGPT's models.
        AZURE: Represents the Azure's models.
        OLLAMA: Represents the Ollama's models.
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    SPARK = "spark"
    ZHIPUAI = "zhipuai"
    FIREWORKS = "fireworks"
    OPEN_LLM = "open_llm"
    GEMINI = "gemini"
    METAGPT = "metagpt"
    AZURE = "azure"
    OLLAMA = "ollama"

    def __missing__(self, key):
        """Provides a default value for missing keys.

        Args:
            key: The missing key.

        Returns:
            The default value for missing keys, which is OPENAI.
        """
        return self.OPENAI


class LLMConfig(YamlModel):
    """Configuration for Language Learning Models (LLM).

    This configuration includes various parameters for connecting to and using different LLMs.

    Attributes:
        api_key: The API key for accessing the LLM.
        api_type: The type of LLM to use, defaults to OPENAI.
        base_url: The base URL for the LLM API, defaults to OpenAI's URL.
        api_version: Optional version of the API.
        model: Optional model name to use.
        app_id: Optional application ID.
        api_secret: Optional API secret.
        domain: Optional domain for the LLM.
        max_token: Maximum number of tokens to generate, defaults to 4096.
        temperature: Sampling temperature, defaults to 0.0.
        top_p: Nucleus sampling parameter, defaults to 1.0.
        top_k: Top-k sampling parameter, defaults to 0.
        repetition_penalty: Penalty for repetition, defaults to 1.0.
        stop: Optional stopping criteria.
        presence_penalty: Penalty for presence, defaults to 0.0.
        frequency_penalty: Penalty for frequency, defaults to 0.0.
        best_of: Optional parameter for generating multiple outputs and choosing the best.
        n: Optional number of completions to generate.
        stream: Whether to stream the results, defaults to False.
        logprobs: Optional parameter to return log probabilities.
        top_logprobs: Optional parameter to return top log probabilities.
        timeout: Timeout for API requests, defaults to 60 seconds.
        proxy: Optional proxy to use for API requests.
        calc_usage: Whether to calculate usage, defaults to True.
    """

    api_key: str
    api_type: LLMType = LLMType.OPENAI
    base_url: str = "https://api.openai.com/v1"
    api_version: Optional[str] = None

    model: Optional[str] = None  # also stands for DEPLOYMENT_NAME

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
    stream: bool = False
    logprobs: Optional[bool] = None  # https://cookbook.openai.com/examples/using_logprobs
    top_logprobs: Optional[int] = None
    timeout: int = 60

    # For Network
    proxy: Optional[str] = None

    # Cost Control
    calc_usage: bool = True

    @field_validator("api_key")
    @classmethod
    def check_llm_key(cls, v):
        """Validates the API key.

        Args:
            v: The API key value to validate.

        Raises:
            ValueError: If the API key is not set correctly.

        Returns:
            The validated API key.
        """
        if v in ["", None, "YOUR_API_KEY"]:
            raise ValueError("Please set your API key in config.yaml")
        return v
