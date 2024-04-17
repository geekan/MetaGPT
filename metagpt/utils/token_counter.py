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
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletionChunk

from metagpt.utils.ahttp_client import apost

TOKEN_COSTS = {
    "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
    "gpt-3.5-turbo-0301": {"prompt": 0.0015, "completion": 0.002},
    "gpt-3.5-turbo-0613": {"prompt": 0.0015, "completion": 0.002},
    "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
    "gpt-3.5-turbo-16k-0613": {"prompt": 0.003, "completion": 0.004},
    "gpt-35-turbo": {"prompt": 0.0015, "completion": 0.002},
    "gpt-35-turbo-16k": {"prompt": 0.003, "completion": 0.004},
    "gpt-3.5-turbo-1106": {"prompt": 0.001, "completion": 0.002},
    "gpt-3.5-turbo-0125": {"prompt": 0.001, "completion": 0.002},
    "gpt-4-0314": {"prompt": 0.03, "completion": 0.06},
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-4-32k": {"prompt": 0.06, "completion": 0.12},
    "gpt-4-32k-0314": {"prompt": 0.06, "completion": 0.12},
    "gpt-4-0613": {"prompt": 0.06, "completion": 0.12},
    "gpt-4-turbo-preview": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-0125-preview": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-1106-preview": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-vision-preview": {"prompt": 0.01, "completion": 0.03},  # TODO add extra image price calculator
    "gpt-4-1106-vision-preview": {"prompt": 0.01, "completion": 0.03},
    "text-embedding-ada-002": {"prompt": 0.0004, "completion": 0.0},
    "glm-3-turbo": {"prompt": 0.0007, "completion": 0.0007},  # 128k version, prompt + completion tokens=0.005￥/k-tokens
    "glm-4": {"prompt": 0.014, "completion": 0.014},  # 128k version, prompt + completion tokens=0.1￥/k-tokens
    "gemini-pro": {"prompt": 0.00025, "completion": 0.0005},
    "moonshot-v1-8k": {"prompt": 0.012, "completion": 0.012},  # prompt + completion tokens=0.012￥/k-tokens
    "moonshot-v1-32k": {"prompt": 0.024, "completion": 0.024},
    "moonshot-v1-128k": {"prompt": 0.06, "completion": 0.06},
    "open-mistral-7b": {"prompt": 0.00025, "completion": 0.00025},
    "open-mixtral-8x7b": {"prompt": 0.0007, "completion": 0.0007},
    "mistral-small-latest": {"prompt": 0.002, "completion": 0.006},
    "mistral-medium-latest": {"prompt": 0.0027, "completion": 0.0081},
    "mistral-large-latest": {"prompt": 0.008, "completion": 0.024},
    "claude-instant-1.2": {"prompt": 0.0008, "completion": 0.0024},
    "claude-2.0": {"prompt": 0.008, "completion": 0.024},
    "claude-2.1": {"prompt": 0.008, "completion": 0.024},
    "claude-3-sonnet-20240229": {"prompt": 0.003, "completion": 0.015},
    "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
    "yi-34b-chat-0205": {"prompt": 0.0003, "completion": 0.0003},
    "yi-34b-chat-200k": {"prompt": 0.0017, "completion": 0.0017},
    "microsoft/wizardlm-2-8x22b": {"prompt": 0.00108, "completion": 0.00108},  # for openrouter, start
    "openai/gpt-3.5-turbo-0125": {"prompt": 0.0005, "completion": 0.0015},
    "openai/gpt-4-turbo-preview": {"prompt": 0.01, "completion": 0.03},
}


"""
QianFan Token Price https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hlrk4akp7#tokens%E5%90%8E%E4%BB%98%E8%B4%B9
Due to QianFan has multi price strategies, we unify `Tokens post-payment` as a statistical method.
"""
QIANFAN_MODEL_TOKEN_COSTS = {
    "ERNIE-Bot-4": {"prompt": 0.017, "completion": 0.017},
    "ERNIE-Bot-8k": {"prompt": 0.0034, "completion": 0.0067},
    "ERNIE-Bot": {"prompt": 0.0017, "completion": 0.0017},
    "ERNIE-Bot-turbo": {"prompt": 0.0011, "completion": 0.0011},
    "EB-turbo-AppBuilder": {"prompt": 0.0011, "completion": 0.0011},
    "ERNIE-Speed": {"prompt": 0.00056, "completion": 0.0011},
    "BLOOMZ-7B": {"prompt": 0.00056, "completion": 0.00056},
    "Llama-2-7B-Chat": {"prompt": 0.00056, "completion": 0.00056},
    "Llama-2-13B-Chat": {"prompt": 0.00084, "completion": 0.00084},
    "Llama-2-70B-Chat": {"prompt": 0.0049, "completion": 0.0049},
    "ChatGLM2-6B-32K": {"prompt": 0.00056, "completion": 0.00056},
    "AquilaChat-7B": {"prompt": 0.00056, "completion": 0.00056},
    "Mixtral-8x7B-Instruct": {"prompt": 0.0049, "completion": 0.0049},
    "SQLCoder-7B": {"prompt": 0.00056, "completion": 0.00056},
    "CodeLlama-7B-Instruct": {"prompt": 0.00056, "completion": 0.00056},
    "XuanYuan-70B-Chat-4bit": {"prompt": 0.0049, "completion": 0.0049},
    "Qianfan-BLOOMZ-7B-compressed": {"prompt": 0.00056, "completion": 0.00056},
    "Qianfan-Chinese-Llama-2-7B": {"prompt": 0.00056, "completion": 0.00056},
    "Qianfan-Chinese-Llama-2-13B": {"prompt": 0.00084, "completion": 0.00084},
    "ChatLaw": {"prompt": 0.0011, "completion": 0.0011},
    "Yi-34B-Chat": {"prompt": 0.0, "completion": 0.0},
}

QIANFAN_ENDPOINT_TOKEN_COSTS = {
    "completions_pro": QIANFAN_MODEL_TOKEN_COSTS["ERNIE-Bot-4"],
    "ernie_bot_8k": QIANFAN_MODEL_TOKEN_COSTS["ERNIE-Bot-8k"],
    "completions": QIANFAN_MODEL_TOKEN_COSTS["ERNIE-Bot"],
    "eb-instant": QIANFAN_MODEL_TOKEN_COSTS["ERNIE-Bot-turbo"],
    "ai_apaas": QIANFAN_MODEL_TOKEN_COSTS["EB-turbo-AppBuilder"],
    "ernie_speed": QIANFAN_MODEL_TOKEN_COSTS["ERNIE-Speed"],
    "bloomz_7b1": QIANFAN_MODEL_TOKEN_COSTS["BLOOMZ-7B"],
    "llama_2_7b": QIANFAN_MODEL_TOKEN_COSTS["Llama-2-7B-Chat"],
    "llama_2_13b": QIANFAN_MODEL_TOKEN_COSTS["Llama-2-13B-Chat"],
    "llama_2_70b": QIANFAN_MODEL_TOKEN_COSTS["Llama-2-70B-Chat"],
    "chatglm2_6b_32k": QIANFAN_MODEL_TOKEN_COSTS["ChatGLM2-6B-32K"],
    "aquilachat_7b": QIANFAN_MODEL_TOKEN_COSTS["AquilaChat-7B"],
    "mixtral_8x7b_instruct": QIANFAN_MODEL_TOKEN_COSTS["Mixtral-8x7B-Instruct"],
    "sqlcoder_7b": QIANFAN_MODEL_TOKEN_COSTS["SQLCoder-7B"],
    "codellama_7b_instruct": QIANFAN_MODEL_TOKEN_COSTS["CodeLlama-7B-Instruct"],
    "xuanyuan_70b_chat": QIANFAN_MODEL_TOKEN_COSTS["XuanYuan-70B-Chat-4bit"],
    "qianfan_bloomz_7b_compressed": QIANFAN_MODEL_TOKEN_COSTS["Qianfan-BLOOMZ-7B-compressed"],
    "qianfan_chinese_llama_2_7b": QIANFAN_MODEL_TOKEN_COSTS["Qianfan-Chinese-Llama-2-7B"],
    "qianfan_chinese_llama_2_13b": QIANFAN_MODEL_TOKEN_COSTS["Qianfan-Chinese-Llama-2-13B"],
    "chatlaw": QIANFAN_MODEL_TOKEN_COSTS["ChatLaw"],
    "yi_34b_chat": QIANFAN_MODEL_TOKEN_COSTS["Yi-34B-Chat"],
}

"""
DashScope Token price https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-thousand-questions-metering-and-billing
Different model has different detail page. Attention, some model are free for a limited time.
"""
DASHSCOPE_TOKEN_COSTS = {
    "qwen-turbo": {"prompt": 0.0011, "completion": 0.0011},
    "qwen-plus": {"prompt": 0.0028, "completion": 0.0028},
    "qwen-max": {"prompt": 0.0, "completion": 0.0},
    "qwen-max-1201": {"prompt": 0.0, "completion": 0.0},
    "qwen-max-longcontext": {"prompt": 0.0, "completion": 0.0},
    "llama2-7b-chat-v2": {"prompt": 0.0, "completion": 0.0},
    "llama2-13b-chat-v2": {"prompt": 0.0, "completion": 0.0},
    "qwen-72b-chat": {"prompt": 0.0, "completion": 0.0},
    "qwen-14b-chat": {"prompt": 0.0011, "completion": 0.0011},
    "qwen-7b-chat": {"prompt": 0.00084, "completion": 0.00084},
    "qwen-1.8b-chat": {"prompt": 0.0, "completion": 0.0},
    "baichuan2-13b-chat-v1": {"prompt": 0.0011, "completion": 0.0011},
    "baichuan2-7b-chat-v1": {"prompt": 0.00084, "completion": 0.00084},
    "baichuan-7b-v1": {"prompt": 0.0, "completion": 0.0},
    "chatglm-6b-v2": {"prompt": 0.0011, "completion": 0.0011},
    "chatglm3-6b": {"prompt": 0.0, "completion": 0.0},
    "ziya-llama-13b-v1": {"prompt": 0.0, "completion": 0.0},  # no price page, judge it as free
    "dolly-12b-v2": {"prompt": 0.0, "completion": 0.0},
    "belle-llama-13b-2m-v1": {"prompt": 0.0, "completion": 0.0},
    "moss-moon-003-sft-v1": {"prompt": 0.0, "completion": 0.0},
    "chatyuan-large-v2": {"prompt": 0.0, "completion": 0.0},
    "billa-7b-sft-v1": {"prompt": 0.0, "completion": 0.0},
}


FIREWORKS_GRADE_TOKEN_COSTS = {
    "-1": {"prompt": 0.0, "completion": 0.0},  # abnormal condition
    "16": {"prompt": 0.2, "completion": 0.8},  # 16 means model size <= 16B; 0.2 means $0.2/1M tokens
    "80": {"prompt": 0.7, "completion": 2.8},  # 80 means 16B < model size <= 80B
    "mixtral-8x7b": {"prompt": 0.4, "completion": 1.6},
}

# https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo
TOKEN_MAX = {
    "gpt-4-0125-preview": 128000,
    "gpt-4-turbo-preview": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4-1106-preview": 128000,
    "gpt-4-vision-preview": 128000,
    "gpt-4-1106-vision-preview": 128000,
    "gpt-4": 8192,
    "gpt-4-0613": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-32k-0613": 32768,
    "gpt-3.5-turbo-0125": 16385,
    "gpt-3.5-turbo": 16385,
    "gpt-3.5-turbo-1106": 16385,
    "gpt-3.5-turbo-instruct": 4096,
    "gpt-3.5-turbo-16k": 16385,
    "gpt-3.5-turbo-0613": 4096,
    "gpt-3.5-turbo-16k-0613": 16385,
    "text-embedding-ada-002": 8192,
    "glm-3-turbo": 128000,
    "glm-4": 128000,
    "gemini-pro": 32768,
    "moonshot-v1-8k": 8192,
    "moonshot-v1-32k": 32768,
    "moonshot-v1-128k": 128000,
    "open-mistral-7b": 8192,
    "open-mixtral-8x7b": 32768,
    "mistral-small-latest": 32768,
    "mistral-medium-latest": 32768,
    "mistral-large-latest": 32768,
    "claude-instant-1.2": 100000,
    "claude-2.0": 100000,
    "claude-2.1": 200000,
    "claude-3-sonnet-20240229": 200000,
    "claude-3-opus-20240229": 200000,
    "yi-34b-chat-0205": 4000,
    "yi-34b-chat-200k": 200000,
    "microsoft/wizardlm-2-8x22b": 65536,
    "openai/gpt-3.5-turbo-0125": 16385,
    "openai/gpt-4-turbo-preview": 128000,
}


def count_message_tokens(messages, model="gpt-3.5-turbo-0125"):
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
        "gpt-3.5-turbo-0125",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        "gpt-4-turbo",
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
        print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0125.")
        return count_message_tokens(messages, model="gpt-3.5-turbo-0125")
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
            f"See https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken "
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


async def get_openrouter_tokens(chunk: ChatCompletionChunk) -> CompletionUsage:
    """refs to https://openrouter.ai/docs#querying-cost-and-stats"""
    url = f"https://openrouter.ai/api/v1/generation?id={chunk.id}"
    resp = await apost(url=url, as_json=True)
    tokens_prompt = resp.get("tokens_prompt", 0)
    completion_tokens = resp.get("tokens_completion", 0)
    usage = CompletionUsage(
        prompt_tokens=tokens_prompt, completion_tokens=completion_tokens, total_tokens=tokens_prompt + completion_tokens
    )
    return usage
