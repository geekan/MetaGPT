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
import anthropic
import tiktoken

from metagpt.logs import logger

TOKEN_COSTS = {
    "anthropic/claude-3.5-sonnet": {"prompt": 0.003, "completion": 0.015},
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
    "gpt-4-1106-preview": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-0125-preview": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-turbo-2024-04-09": {"prompt": 0.01, "completion": 0.03},
    "gpt-4-vision-preview": {"prompt": 0.01, "completion": 0.03},  # TODO add extra image price calculator
    "gpt-4-1106-vision-preview": {"prompt": 0.01, "completion": 0.03},
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-4o-mini-2024-07-18": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-4o-2024-05-13": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-2024-08-06": {"prompt": 0.0025, "completion": 0.01},
    "o1-preview": {"prompt": 0.015, "completion": 0.06},
    "o1-preview-2024-09-12": {"prompt": 0.015, "completion": 0.06},
    "o1-mini": {"prompt": 0.003, "completion": 0.012},
    "o1-mini-2024-09-12": {"prompt": 0.003, "completion": 0.012},
    "text-embedding-ada-002": {"prompt": 0.0004, "completion": 0.0},
    "glm-3-turbo": {"prompt": 0.0007, "completion": 0.0007},  # 128k version, prompt + completion tokens=0.005￥/k-tokens
    "glm-4": {"prompt": 0.014, "completion": 0.014},  # 128k version, prompt + completion tokens=0.1￥/k-tokens
    "glm-4-flash": {"prompt": 0, "completion": 0},
    "glm-4-plus": {"prompt": 0.007, "completion": 0.007},
    "gemini-1.5-flash": {"prompt": 0.000075, "completion": 0.0003},
    "gemini-1.5-pro": {"prompt": 0.0035, "completion": 0.0105},
    "gemini-1.0-pro": {"prompt": 0.0005, "completion": 0.0015},
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
    "claude-3-5-sonnet": {"prompt": 0.003, "completion": 0.015},
    "claude-3-5-sonnet-v2": {"prompt": 0.003, "completion": 0.015},  # alias of newer 3.5 sonnet
    "claude-3-5-sonnet-20240620": {"prompt": 0.003, "completion": 0.015},
    "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
    "claude-3-haiku-20240307": {"prompt": 0.00025, "completion": 0.00125},
    "claude-3-7-sonnet-20250219": {"prompt": 0.003, "completion": 0.015},
    "yi-34b-chat-0205": {"prompt": 0.0003, "completion": 0.0003},
    "yi-34b-chat-200k": {"prompt": 0.0017, "completion": 0.0017},
    "openai/gpt-4": {"prompt": 0.03, "completion": 0.06},  # start, for openrouter
    "openai/gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "openai/gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "openai/gpt-4o-2024-05-13": {"prompt": 0.005, "completion": 0.015},
    "openai/gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "openai/gpt-4o-mini-2024-07-18": {"prompt": 0.00015, "completion": 0.0006},
    "google/gemini-flash-1.5": {"prompt": 0.00025, "completion": 0.00075},
    "deepseek/deepseek-coder": {"prompt": 0.00014, "completion": 0.00028},
    "deepseek/deepseek-chat": {"prompt": 0.00014, "completion": 0.00028},  # end, for openrouter
    "yi-large": {"prompt": 0.0028, "completion": 0.0028},
    "microsoft/wizardlm-2-8x22b": {"prompt": 0.00108, "completion": 0.00108},  # for openrouter, start
    "meta-llama/llama-3-70b-instruct": {"prompt": 0.008, "completion": 0.008},
    "llama3-70b-8192": {"prompt": 0.0059, "completion": 0.0079},
    "openai/gpt-3.5-turbo-0125": {"prompt": 0.0005, "completion": 0.0015},
    "openai/gpt-4-turbo-preview": {"prompt": 0.01, "completion": 0.03},
    "openai/o1-preview": {"prompt": 0.015, "completion": 0.06},
    "openai/o1-mini": {"prompt": 0.003, "completion": 0.012},
    "anthropic/claude-3-opus": {"prompt": 0.015, "completion": 0.075},
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {"prompt": 0.003, "completion": 0.015},
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": {"prompt": 0.003, "completion": 0.015},
    "anthropic/claude-3.7-sonnet": {"prompt": 0.003, "completion": 0.015},
    "anthropic/claude-3.7-sonnet:beta": {"prompt": 0.003, "completion": 0.015},
    "anthropic/claude-3.7-sonnet:thinking": {"prompt": 0.003, "completion": 0.015},
    "anthropic.claude-3-7-sonnet-20250219-v1:0": {"prompt": 0.003, "completion": 0.015},
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0": {"prompt": 0.003, "completion": 0.015},
    "google/gemini-pro-1.5": {"prompt": 0.0025, "completion": 0.0075},  # for openrouter, end
    "deepseek-chat": {"prompt": 0.00027, "completion": 0.0011},
    "deepseek-coder": {"prompt": 0.00027, "completion": 0.0011},
    "deepseek-reasoner": {"prompt": 0.00055, "completion": 0.0022},
    # For ark model https://www.volcengine.com/docs/82379/1099320
    "doubao-lite-4k-240515": {"prompt": 0.000043, "completion": 0.000086},
    "doubao-lite-32k-240515": {"prompt": 0.000043, "completion": 0.000086},
    "doubao-lite-128k-240515": {"prompt": 0.00011, "completion": 0.00014},
    "doubao-pro-4k-240515": {"prompt": 0.00011, "completion": 0.00029},
    "doubao-pro-32k-240515": {"prompt": 0.00011, "completion": 0.00029},
    "doubao-pro-128k-240515": {"prompt": 0.0007, "completion": 0.0013},
    "llama3-70b-llama3-70b-instruct": {"prompt": 0.0, "completion": 0.0},
    "llama3-8b-llama3-8b-instruct": {"prompt": 0.0, "completion": 0.0},
    "llama-4-Scout-17B-16E-Instruct-FP8" : {"prompt": 0.0, "completion": 0.0}, # start, for Llama API
    "llama-4-Maverick-17B-128E-Instruct-FP8": {"prompt": 0.0, "completion": 0.0},
    "llama-3.3-8B-Instruct": {"prompt": 0.0, "completion": 0.0},
    "llama-3.3-70B-Instruct": {"prompt": 0.0, "completion": 0.0}, # end, for Llama API
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
Some new model published by Alibaba will be prioritized to be released on the Model Studio instead of the Dashscope.
Token price on Model Studio shows on https://help.aliyun.com/zh/model-studio/getting-started/models#ced16cb6cdfsy
"""
DASHSCOPE_TOKEN_COSTS = {
    "qwen2.5-72b-instruct": {"prompt": 0.00057, "completion": 0.0017},  # per 1k tokens
    "qwen2.5-32b-instruct": {"prompt": 0.0005, "completion": 0.001},
    "qwen2.5-14b-instruct": {"prompt": 0.00029, "completion": 0.00086},
    "qwen2.5-7b-instruct": {"prompt": 0.00014, "completion": 0.00029},
    "qwen2.5-3b-instruct": {"prompt": 0.0, "completion": 0.0},
    "qwen2.5-1.5b-instruct": {"prompt": 0.0, "completion": 0.0},
    "qwen2.5-0.5b-instruct": {"prompt": 0.0, "completion": 0.0},
    "qwen2-72b-instruct": {"prompt": 0.000714, "completion": 0.001428},
    "qwen2-57b-a14b-instruct": {"prompt": 0.0005, "completion": 0.001},
    "qwen2-7b-instruct": {"prompt": 0.000143, "completion": 0.000286},
    "qwen2-1.5b-instruct": {"prompt": 0, "completion": 0},
    "qwen2-0.5b-instruct": {"prompt": 0, "completion": 0},
    "qwen1.5-110b-chat": {"prompt": 0.001, "completion": 0.002},
    "qwen1.5-72b-chat": {"prompt": 0.000714, "completion": 0.001428},
    "qwen1.5-32b-chat": {"prompt": 0.0005, "completion": 0.001},
    "qwen1.5-14b-chat": {"prompt": 0.000286, "completion": 0.000571},
    "qwen1.5-7b-chat": {"prompt": 0.000143, "completion": 0.000286},
    "qwen1.5-1.8b-chat": {"prompt": 0, "completion": 0},
    "qwen1.5-0.5b-chat": {"prompt": 0, "completion": 0},
    "qwen-turbo": {"prompt": 0.00028, "completion": 0.00083},
    "qwen-long": {"prompt": 0.00007, "completion": 0.00028},
    "qwen-plus": {"prompt": 0.00055, "completion": 0.00166},
    "qwen-max": {"prompt": 0.0055, "completion": 0.0166},
    "qwen-max-0428": {"prompt": 0.0055, "completion": 0.0166},
    "qwen-max-0403": {"prompt": 0.0055, "completion": 0.0166},
    "qwen-max-0107": {"prompt": 0.0055, "completion": 0.0166},
    "qwen-max-1201": {"prompt": 0.0166, "completion": 0.0166},
    "qwen-max-longcontext": {"prompt": 0.0055, "completion": 0.0166},
    "llama2-7b-chat-v2": {"prompt": 0.0, "completion": 0.0},
    "llama2-13b-chat-v2": {"prompt": 0.0, "completion": 0.0},
    "qwen-72b-chat": {"prompt": 0.0028, "completion": 0.0028},
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

# https://console.volcengine.com/ark/region:ark+cn-beijing/model
DOUBAO_TOKEN_COSTS = {
    "doubao-lite": {"prompt": 0.000043, "completion": 0.000086},
    "doubao-lite-128k": {"prompt": 0.00011, "completion": 0.00014},
    "doubao-pro": {"prompt": 0.00011, "completion": 0.00029},
    "doubao-pro-128k": {"prompt": 0.00071, "completion": 0.0013},
    "doubao-pro-256k": {"prompt": 0.00071, "completion": 0.0013},
}

# https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo
TOKEN_MAX = {
    "o1-preview": 128000,
    "o1-preview-2024-09-12": 128000,
    "o1-mini": 128000,
    "o1-mini-2024-09-12": 128000,
    "gpt-4o": 128000,
    "gpt-4o-2024-05-13": 128000,
    "gpt-4o-2024-08-06": 128000,
    "gpt-4o-mini-2024-07-18": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo-2024-04-09": 128000,
    "gpt-4-0125-preview": 128000,
    "gpt-4-turbo-preview": 128000,
    "gpt-4-1106-preview": 128000,
    "gpt-4-turbo": 128000,
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
    "gemini-1.5-flash": 1000000,
    "gemini-1.5-pro": 2000000,
    "gemini-1.0-pro": 32000,
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
    "claude-3-5-sonnet-20240620": 200000,
    "claude-3-haiku-20240307": 200000,
    "yi-34b-chat-0205": 4000,
    "yi-34b-chat-200k": 200000,
    "openai/gpt-4": 8192,  # start, for openrouter
    "openai/gpt-4-turbo": 128000,
    "openai/gpt-4o": 128000,
    "openai/gpt-4o-2024-05-13": 128000,
    "openai/gpt-4o-mini": 128000,
    "openai/gpt-4o-mini-2024-07-18": 128000,
    "google/gemini-flash-1.5": 2800000,
    "deepseek/deepseek-coder": 128000,
    "deepseek/deepseek-chat": 128000,  # end, for openrouter
    "deepseek-chat": 128000,
    "deepseek-coder": 128000,
    "deepseek-ai/DeepSeek-Coder-V2-Instruct": 32000,  # siliconflow
    "yi-large": 16385,
    "microsoft/wizardlm-2-8x22b": 65536,
    "meta-llama/llama-3-70b-instruct": 8192,
    "llama3-70b-8192": 8192,
    "openai/gpt-3.5-turbo-0125": 16385,
    "openai/gpt-4-turbo-preview": 128000,
    "openai/o1-preview": 128000,
    "openai/o1-mini": 128000,
    "anthropic/claude-3-opus": 200000,
    "anthropic/claude-3.5-sonnet": 200000,
    "google/gemini-pro-1.5": 4000000,
    "doubao-lite-4k-240515": 4000,
    "doubao-lite-32k-240515": 32000,
    "doubao-lite-128k-240515": 128000,
    "doubao-pro-4k-240515": 4000,
    "doubao-pro-32k-240515": 32000,
    "doubao-pro-128k-240515": 128000,
    # Qwen https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-7b-14b-72b-api-detailes?spm=a2c4g.11186623.0.i20
    "qwen2.5-72b-instruct": 131072,
    "qwen2.5-32b-instruct": 131072,
    "qwen2.5-14b-instruct": 131072,
    "qwen2.5-7b-instruct": 131072,
    "qwen2.5-3b-instruct": 32768,
    "qwen2.5-1.5b-instruct": 32768,
    "qwen2.5-0.5b-instruct": 32768,
    "qwen2-57b-a14b-instruct": 32768,
    "qwen2-72b-instruct": 131072,
    "qwen2-7b-instruct": 32768,
    "qwen2-1.5b-instruct": 32768,
    "qwen2-0.5b-instruct": 32768,
    "qwen1.5-110b-chat": 32000,
    "qwen1.5-72b-chat": 32000,
    "qwen1.5-32b-chat": 32000,
    "qwen1.5-14b-chat": 8000,
    "qwen1.5-7b-chat": 32000,
    "qwen1.5-1.8b-chat": 32000,
    "qwen1.5-0.5b-chat": 32000,
    "codeqwen1.5-7b-chat": 64000,
    "qwen-72b-chat": 32000,
    "qwen-14b-chat": 8000,
    "qwen-7b-chat": 32000,
    "qwen-1.8b-longcontext-chat": 32000,
    "qwen-1.8b-chat": 8000,
}

# For Amazon Bedrock US region
# See https://aws.amazon.com/cn/bedrock/pricing/

BEDROCK_TOKEN_COSTS = {
    "amazon.titan-tg1-large": {"prompt": 0.0008, "completion": 0.0008},
    "amazon.titan-text-express-v1": {"prompt": 0.0008, "completion": 0.0008},
    "amazon.titan-text-express-v1:0:8k": {"prompt": 0.0008, "completion": 0.0008},
    "amazon.titan-text-lite-v1:0:4k": {"prompt": 0.0003, "completion": 0.0004},
    "amazon.titan-text-lite-v1": {"prompt": 0.0003, "completion": 0.0004},
    "anthropic.claude-instant-v1": {"prompt": 0.0008, "completion": 0.00024},
    "anthropic.claude-instant-v1:2:100k": {"prompt": 0.0008, "completion": 0.00024},
    "anthropic.claude-v1": {"prompt": 0.008, "completion": 0.0024},
    "anthropic.claude-v2": {"prompt": 0.008, "completion": 0.0024},
    "anthropic.claude-v2:1": {"prompt": 0.008, "completion": 0.0024},
    "anthropic.claude-v2:0:18k": {"prompt": 0.008, "completion": 0.0024},
    "anthropic.claude-v2:1:200k": {"prompt": 0.008, "completion": 0.0024},
    "anthropic.claude-3-sonnet-20240229-v1:0": {"prompt": 0.003, "completion": 0.015},
    "anthropic.claude-3-sonnet-20240229-v1:0:28k": {"prompt": 0.003, "completion": 0.015},
    "anthropic.claude-3-sonnet-20240229-v1:0:200k": {"prompt": 0.003, "completion": 0.015},
    "anthropic.claude-3-5-sonnet-20240620-v1:0": {"prompt": 0.003, "completion": 0.015},
    "anthropic.claude-3-haiku-20240307-v1:0": {"prompt": 0.00025, "completion": 0.00125},
    "anthropic.claude-3-haiku-20240307-v1:0:48k": {"prompt": 0.00025, "completion": 0.00125},
    "anthropic.claude-3-haiku-20240307-v1:0:200k": {"prompt": 0.00025, "completion": 0.00125},
    # currently (2024-4-29) only available at US West (Oregon) AWS Region.
    "anthropic.claude-3-opus-20240229-v1:0": {"prompt": 0.015, "completion": 0.075},
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {"prompt": 0.003, "completion": 0.015},
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": {"prompt": 0.003, "completion": 0.015},
    "anthropic.claude-3-7-sonnet-20250219-v1:0": {"prompt": 0.003, "completion": 0.015},
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0": {"prompt": 0.003, "completion": 0.015},
    "cohere.command-text-v14": {"prompt": 0.0015, "completion": 0.0015},
    "cohere.command-text-v14:7:4k": {"prompt": 0.0015, "completion": 0.0015},
    "cohere.command-light-text-v14": {"prompt": 0.0003, "completion": 0.0003},
    "cohere.command-light-text-v14:7:4k": {"prompt": 0.0003, "completion": 0.0003},
    "meta.llama2-13b-chat-v1:0:4k": {"prompt": 0.00075, "completion": 0.001},
    "meta.llama2-13b-chat-v1": {"prompt": 0.00075, "completion": 0.001},
    "meta.llama2-70b-v1": {"prompt": 0.00195, "completion": 0.00256},
    "meta.llama2-70b-v1:0:4k": {"prompt": 0.00195, "completion": 0.00256},
    "meta.llama2-70b-chat-v1": {"prompt": 0.00195, "completion": 0.00256},
    "meta.llama2-70b-chat-v1:0:4k": {"prompt": 0.00195, "completion": 0.00256},
    "meta.llama3-8b-instruct-v1:0": {"prompt": 0.0004, "completion": 0.0006},
    "meta.llama3-70b-instruct-v1:0": {"prompt": 0.00265, "completion": 0.0035},
    "mistral.mistral-7b-instruct-v0:2": {"prompt": 0.00015, "completion": 0.0002},
    "mistral.mixtral-8x7b-instruct-v0:1": {"prompt": 0.00045, "completion": 0.0007},
    "mistral.mistral-large-2402-v1:0": {"prompt": 0.008, "completion": 0.024},
    "ai21.j2-grande-instruct": {"prompt": 0.0125, "completion": 0.0125},
    "ai21.j2-jumbo-instruct": {"prompt": 0.0188, "completion": 0.0188},
    "ai21.j2-mid": {"prompt": 0.0125, "completion": 0.0125},
    "ai21.j2-mid-v1": {"prompt": 0.0125, "completion": 0.0125},
    "ai21.j2-ultra": {"prompt": 0.0188, "completion": 0.0188},
    "ai21.j2-ultra-v1": {"prompt": 0.0188, "completion": 0.0188},
}

# https://xinghuo.xfyun.cn/sparkapi?scr=price
SPARK_TOKENS = {
    "general": {"prompt": 0.0, "completion": 0.0},  # Spark-Lite
    "generalv2": {"prompt": 0.0188, "completion": 0.0188},  # Spark V2.0
    "generalv3": {"prompt": 0.0035, "completion": 0.0035},  # Spark Pro
    "generalv3.5": {"prompt": 0.0035, "completion": 0.0035},  # Spark3.5 Max
}


def count_claude_message_tokens(messages: list[dict], model: str) -> int:
    # rough estimation for models newer than claude-2.1, needs api_key or auth_token
    ac = anthropic.Client()
    system_prompt = ""
    new_messages = []
    for msg in messages:
        if msg.get("role") == "system":
            system_prompt = msg.get("content")
        else:
            new_messages.append(msg)
    num_tokens = ac.beta.messages.count_tokens(messages=new_messages, model=model, system=system_prompt)
    return num_tokens.input_tokens


def count_message_tokens(messages, model="gpt-3.5-turbo-0125"):
    """Return the number of tokens used by a list of messages."""
    if "claude" in model:
        num_tokens = count_claude_message_tokens(messages, model)
        return num_tokens
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.info(f"Warning: model {model} not found in tiktoken. Using cl100k_base encoding.")
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
        "gpt-4-turbo",
        "gpt-4-vision-preview",
        "gpt-4-1106-vision-preview",
        "gpt-4o",
        "gpt-4o-2024-05-13",
        "gpt-4o-2024-08-06",
        "gpt-4o-mini",
        "gpt-4o-mini-2024-07-18",
        "o1-preview",
        "o1-preview-2024-09-12",
        "o1-mini",
        "o1-mini-2024-09-12",
    }:
        tokens_per_message = 3  # # every reply is primed with <|start|>assistant<|message|>
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" == model:
        logger.info("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0125.")
        return count_message_tokens(messages, model="gpt-3.5-turbo-0125")
    elif "gpt-4" == model:
        logger.info("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
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


def count_output_tokens(string: str, model: str) -> int:
    """
    Returns the number of tokens in a text string.

    Args:
        string (str): The text string.
        model (str): The name of the encoding to use. (e.g., "gpt-3.5-turbo")

    Returns:
        int: The number of tokens in the text string.
    """
    if "claude" in model:
        messages = [{"role": "assistant", "content": string}]
        num_tokens = count_claude_message_tokens(messages, model)
        return num_tokens
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.info(f"Warning: model {model} not found in tiktoken. Using cl100k_base encoding.")
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
    return TOKEN_MAX[model] - count_message_tokens(messages, model) - 1
