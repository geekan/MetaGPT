#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 22:59
@Author  : alexanderwu
@File    : __init__.py
"""
import importlib
from metagpt.configs.llm_config import LLMType, LLMModuleMap

class LLMFactory:
    def __init__(self, module_name, instance_name):
        self.module_name = module_name
        self.instance_name = instance_name
        self._module = None

    def __getattr__(self, name):
        if self._module is None:
            self._module = importlib.import_module(self.module_name)
        return getattr(self._module, name)
    
    def __instancecheck__(self, instance):
        if self._module is None:
            self._module = importlib.import_module(self.module_name)
        return isinstance(instance, getattr(self._module, self.instance_name))
    
    def __call__(self, config):
        # Import the module when it鈥檚 called for the first time
        if self._module is None:
            self._module = importlib.import_module(self.module_name)
        
        # Create an instance of the specified class from the module with the given config
        return getattr(self._module, self.instance_name)(config)
    
def create_llm_symbol(llm_configurations):
    factories = {name: LLMFactory(LLMModuleMap[llm_type], name) for llm_type, name in llm_configurations}
    # Add the factory created llm objects to the global namespace
    globals().update(factories)
    return factories.keys()

# List of LLM configurations
llm_configurations = [
    (LLMType.GEMINI, "GeminiLLM"),
    (LLMType.OLLAMA, "OllamaLLM"),
    (LLMType.OPENAI, "OpenAILLM"),
    (LLMType.ZHIPUAI, "ZhiPuAILLM"),
    (LLMType.AZURE, "AzureOpenAILLM"),
    (LLMType.METAGPT, "MetaGPTLLM"),
    (LLMType.HUMAN, "HumanProvider"),
    (LLMType.SPARK, "SparkLLM"),
    (LLMType.QIANFAN, "QianFanLLM"),
    (LLMType.DASHSCOPE, "DashScopeLLM"),
    (LLMType.ANTHROPIC, "AnthropicLLM"),
    (LLMType.BEDROCK, "BedrockLLM"),
    (LLMType.ARK, "ArkLLM"),
    (LLMType.FIREWORKS, "FireworksLLM"),
    (LLMType.OPEN_LLM, "OpenLLM"),
    (LLMType.MOONSHOT, "MoonshotLLM"),
    (LLMType.MISTRAL, "MistralLLM"),
    (LLMType.YI, "YiLLM"),
    (LLMType.OPENROUTER, "OpenRouterLLM"),
    (LLMType.CLAUDE, "ClaudeLLM"),
]

# Create all LLMFactory instances and get created symbols
__all__ = create_llm_symbol(llm_configurations)