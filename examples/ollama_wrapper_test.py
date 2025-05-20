#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Test script for Ollama with third-party URL wrapper

import asyncio
import os
import sys

# Add the project root to the path so we can import metagpt
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.ollama_api import OllamaLLM


async def test_ollama_wrapper():
    """Test Ollama with a third-party URL wrapper"""
    print("Testing Ollama with third-party URL wrapper...")
    
    # Configuration for direct Ollama (for comparison)
    direct_config = LLMConfig(
        api_type=LLMType.OLLAMA,
        model="llama2",  # Change to a model you have installed
        base_url="http://localhost:11434",
        api_key="not-needed-for-ollama",
    )
    
    # Configuration for Ollama with wrapper (with /api in URL)
    wrapper_config_with_api = LLMConfig(
        api_type=LLMType.OLLAMA,
        model="llama2",  # Change to a model you have installed
        base_url="http://localhost:8989/ollama/api",  # Your wrapper URL with /api
        api_key="not-needed-for-ollama",
    )
    
    # Configuration for Ollama with wrapper (without /api in URL)
    wrapper_config_without_api = LLMConfig(
        api_type=LLMType.OLLAMA,
        model="llama2",  # Change to a model you have installed
        base_url="http://localhost:8989/ollama",  # Your wrapper URL without /api
        api_key="not-needed-for-ollama",
    )
    
    # Choose which configuration to test
    # config = direct_config
    config = wrapper_config_with_api
    # config = wrapper_config_without_api
    
    # Initialize the Ollama LLM
    ollama = OllamaLLM(config)
    
    # Test the URL construction
    api_url = ollama._get_api_url(ollama.ollama_message.api_suffix)
    print(f"Base URL: {config.base_url}")
    print(f"API suffix: {ollama.ollama_message.api_suffix}")
    print(f"Constructed API URL: {api_url}")
    print(f"Full URL would be: {config.base_url}{api_url}")
    
    # Uncomment to test an actual API call
    # try:
    #     messages = [{"role": "user", "content": "Hello, how are you?"}]
    #     response = await ollama.acompletion(messages)
    #     print("\nAPI Response:")
    #     print(response)
    # except Exception as e:
    #     print(f"\nError during API call: {e}")


if __name__ == "__main__":
    asyncio.run(test_ollama_wrapper())
