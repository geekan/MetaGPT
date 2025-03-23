#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 01:25
@Author  : alexanderwu
@File    : config2.py
"""
from typing import List, Optional

from metagpt.configs.browser_config import BrowserConfig
from metagpt.configs.embedding_config import EmbeddingConfig
from metagpt.configs.omniparse_config import OmniParseConfig
from metagpt.configs.redis_config import RedisConfig
from metagpt.configs.role_custom_config import RoleCustomConfig
from metagpt.configs.s3_config import S3Config
from metagpt.configs.search_config import SearchConfig
from metagpt.core.config import CoreConfig
from metagpt.core.configs.llm_config import LLMConfig, LLMType
from metagpt.core.configs.mermaid_config import MermaidConfig


class Config(CoreConfig):
    """Configurations for MetaGPT"""

    # RAG Embedding
    embedding: EmbeddingConfig = EmbeddingConfig()

    # omniparse
    omniparse: OmniParseConfig = OmniParseConfig()

    # Global Proxy. Will be used if llm.proxy is not set
    proxy: str = ""

    # Tool Parameters
    search: SearchConfig = SearchConfig()
    enable_search: bool = False
    browser: BrowserConfig = BrowserConfig()
    mermaid: MermaidConfig = MermaidConfig()

    # Storage Parameters
    s3: Optional[S3Config] = None
    redis: Optional[RedisConfig] = None

    # Misc Parameters
    enable_longterm_memory: bool = False
    code_validate_k_times: int = 2

    # Will be removed in the future
    metagpt_tti_url: str = ""
    language: str = "English"
    redis_key: str = "placeholder"
    iflytek_app_id: str = ""
    iflytek_api_secret: str = ""
    iflytek_api_key: str = ""
    _extra: dict = dict()  # extra config dict

    # Role's custom configuration
    roles: Optional[List[RoleCustomConfig]] = None

    @property
    def extra(self):
        return self._extra

    @extra.setter
    def extra(self, value: dict):
        self._extra = value

    def get_openai_llm(self) -> Optional[LLMConfig]:
        """Get OpenAI LLMConfig by name. If no OpenAI, raise Exception"""
        if self.llm.api_type == LLMType.OPENAI:
            return self.llm
        return None

    def get_azure_llm(self) -> Optional[LLMConfig]:
        """Get Azure LLMConfig by name. If no Azure, raise Exception"""
        if self.llm.api_type == LLMType.AZURE:
            return self.llm
        return None


config = Config.default()
