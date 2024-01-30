#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/19 17:26
# @Author  : alexanderwu
# @File    : llm_provider_registry.py

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.base_llm import BaseLLM


class LLMProviderRegistry:
    """Registry for LLM providers.

    This class is used to register and retrieve LLM providers based on a key.

    Attributes:
        providers: A dictionary to store provider classes with their corresponding keys.
    """

    def __init__(self):
        """Initializes the LLMProviderRegistry with an empty providers dictionary."""
        self.providers = {}

    def register(self, key, provider_cls):
        """Registers a provider class with a specific key.

        Args:
            key: The key associated with the provider class.
            provider_cls: The provider class to be registered.
        """
        self.providers[key] = provider_cls

    def get_provider(self, enum: LLMType):
        """Retrieves a provider instance according to the enum.

        Args:
            enum: The LLMType enum to retrieve the provider for.

        Returns:
            An instance of the provider associated with the given enum.
        """
        return self.providers[enum]


def register_provider(key):
    """Decorator to register a provider class to the LLMProviderRegistry.

    Args:
        key: The key to register the provider class with.

    Returns:
        The decorator function.
    """

    def decorator(cls):
        LLM_REGISTRY.register(key, cls)
        return cls

    return decorator


def create_llm_instance(config: LLMConfig) -> BaseLLM:
    """Creates an instance of the default LLM provider based on the given configuration.

    Args:
        config: The LLMConfig object containing the configuration for the LLM instance.

    Returns:
        An instance of the BaseLLM provider.
    """
    return LLM_REGISTRY.get_provider(config.api_type)(config)


# Registry instance
LLM_REGISTRY = LLMProviderRegistry()
