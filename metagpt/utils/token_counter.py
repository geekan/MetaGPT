#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/18 00:40
@Author  : alexanderwu
@File    : token_counter.py
ref1: https://openai.com/pricing
ref2: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
ref3: https://github.com/Significant-Gravitas/Auto-GPT/blob/master/autogpt/llm/token_counter.py
ref4: https://github.com/hwchase17/langchain/blob/master/langchain/chat_models/openai.py
ref5: https://ai.google.dev/models/gemini
"""
import tiktoken

TOKEN_COSTS = {
    "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
    "gpt-3.5-turbo-0301": {"prompt": 0.0015, "completion": 0.002},
    "gpt-3.5-turbo-0613": {"prompt": 0.0015, "completion": 0.002},
    "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
    "gpt-3.5-turbo-16k-0613": {"prompt": 0.003, "completion": 0.004},
    "gpt-35-turbo": {"prompt": 0.0015, "completion": 0.002},
    "gpt-35-turbo-16k": {"prompt": 0.003, "completion": 0.004},
    "gpt-3.5-turbo-1106": {"prompt": 0.001, "completion": 0.002},
    "gpt-4-0314": {"prompt": 0.03, "completion": 0.06},
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-4-32k": {"prompt": 0.06, "completion": 0.12},
    "gpt-4-32k-0314": {"prompt": 0.06, "completion": 0.12},
    "gpt-4-0613": {"prompt": 0.06, "completion": 0.12},
    "gpt-4-turbo-preview": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-0125-preview": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-1106-preview": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-vision-preview": {"prompt": 0.01, "completion": 0.03},  # TODO add extra image price calculator
    "gpt-4-1106-vision-preview": {"prompt": 0.01, "completion": 0.03},
    "text-embedding-ada-002": {"prompt": 0.0004, "completion": 0.0},
    "glm-3-turbo": {"prompt": 0.0007, "completion": 0.0007},  # 128k version, prompt + completion tokens=0.005￥/k-tokens
    "glm-4": {"prompt": 0.014, "completion": 0.014},  # 128k version, prompt + completion tokens=0.1￥/k-tokens
    "gemini-pro": {"prompt": 0.00025, "completion": 0.0005},
}


TOKEN_MAX = {
    "gpt-3.5-turbo": 4096,
    "gpt-3.5-turbo-0301": 4096,
    "gpt-3.5-turbo-0613": 4096,
    "gpt-3.5-turbo-16k": 16384,
    "gpt-3.5-turbo-16k-0613": 16384,
    "gpt-35-turbo": 4096,
    "gpt-35-turbo-16k": 16384,
    "gpt-3.5-turbo-1106": 16384,
    "gpt-4-0314": 8192,
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-32k-0314": 32768,
    "gpt-4-0613": 8192,
    "gpt-4-turbo-preview": 128000,
    "gpt-4-0125-preview": 128000,
    "gpt-4-1106-preview": 128000,
    "gpt-4-vision-preview": 128000,
    "gpt-4-1106-vision-preview": 128000,
    "text-embedding-ada-002": 8192,
    "glm-3-turbo": 128000,
    "glm-4": 128000,
    "gemini-pro": 32768,
}


def count_message_tokens(messages, model="gpt-3.5-turbo-0613"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-35-turbo",
        "gpt-35-turbo-16k",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-1106",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        "gpt-4-turbo-preview",
        "gpt-4-0125-preview",
        "gpt-4-1106-preview",
        "gpt-4-vision-preview",
        "gpt-4-1106-vision-preview",
    }:
        tokens_per_message = 3  # # every reply is primed with <|start|>assistant<|message|>
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" == model:
        print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return count_message_tokens(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" == model:
        print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return count_message_tokens(messages, model="gpt-4-0613")
    elif "open-llm-model" == model:
        """
        For self-hosted open_llm api, they include lots of different models. The message tokens calculation is
        inaccurate. It's a reference result.
        """
        tokens_per_message = 0  # ignore conversation message template prefix
        tokens_per_name = 0
    else:
        raise NotImplementedError(
            f"num_tokens_from_messages() is not implemented for model {model}. "
            f"See https://github.com/openai/openai-python/blob/main/chatml.md "
            f"for information on how messages are converted to tokens."
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            content = value
            if isinstance(value, list):
                # for gpt-4v
                for item in value:
                    if isinstance(item, dict) and item.get("type") in ["text"]:
                        content = item.get("text", "")
            num_tokens += len(encoding.encode(content))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def count_string_tokens(string: str, model_name: str) -> int:
    """
    Returns the number of tokens in a text string.

    Args:
        string (str): The text string.
        model_name (str): The name of the encoding to use. (e.g., "gpt-3.5-turbo")

    Returns:
        int: The number of tokens in the text string.
    """
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(string))


def get_max_completion_tokens(messages: list[dict], model: str, default: int) -> int:
    """Calculate the maximum number of completion tokens for a given model and list of messages.

    Args:
        messages: A list of messages.
        model: The model name.

    Returns:
        The maximum number of completion tokens.
    """
    if model not in TOKEN_MAX:
        return default
    return TOKEN_MAX[model] - count_message_tokens(messages) - 1
