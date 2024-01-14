#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19 17:26
@Author  : alexanderwu
@File    : llm_provider_registry.py
"""
from metagpt.config import LLMProviderEnum


class LLMProviderRegistry:
    def __init__(self):
        self.providers = {}

    def register(self, key, provider_cls):
        self.providers[key] = provider_cls

    def get_provider(self, enum: LLMProviderEnum):
        """get provider instance according to the enum"""
        return self.providers[enum]()


# Registry instance
LLM_REGISTRY = LLMProviderRegistry()


def register_provider(key):
    """register provider to registry"""

    def decorator(cls):
        LLM_REGISTRY.register(key, cls)
        return cls

    return decorator
