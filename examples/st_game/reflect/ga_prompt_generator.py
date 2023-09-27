#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: didi
# Date:9.25

import openai
from metagpt.llm import DEFAULT_LLM
# 直接调用Prompt生成
# ga的prompt构建格式和metagpt完全不同。没有办法融合。


# 特殊指令加入Prompt生成


async def final_response(prompt, special_instruction, example_output=None):
    """
    通过将特殊指令加入Prompt生成最终的响应。

    参数：
    - prompt：要生成响应的提示文本。
    - special_instruction：要加入Prompt的特殊指令。
    - example_output（可选）：示例输出的JSON字符串。

    返回：
    生成的最终响应。

    """
    prompt = '"""\n' + prompt + '\n"""\n'
    prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
    if example_output:
        prompt += "Example output json:\n"
        prompt += '{"output": "' + str(example_output) + '"}'
    return await DEFAULT_LLM.aask(prompt)

# prompt填充模板


def prompt_generate(curr_input, prompt_lib_file):
    """
    Takes in the current input (e.g. comment that you want to classifiy) and 
    the path to a prompt file. The prompt file contains the raw str prompt that
    will be used, which contains the following substr: !<INPUT>! -- this 
    function replaces this substr with the actual curr_input to produce the 
    final promopt that will be sent to the GPT3 server. 
    ARGS:
    curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                INPUT, THIS CAN BE A LIST.)
    prompt_lib_file: the path to the promopt file. 
    RETURNS: 
    a str prompt that will be sent to OpenAI's GPT server.  
    """
    if type(curr_input) is type("string"):
        curr_input = [curr_input]
        curr_input = [str(i) for i in curr_input]

    f = open(prompt_lib_file, "r")
    prompt = f.read()
    f.close()
    for count, i in enumerate(curr_input):
        prompt = prompt.replace(f"!<INPUT {count}>!", i)
    if "<commentblockmarker>###</commentblockmarker>" in prompt:
        prompt = prompt.split(
            "<commentblockmarker>###</commentblockmarker>")[1]
    return prompt.strip()

# 使用OpenAI embedding库进行存储


def embedding(query):
    """
    Generates an embedding for the given query.

    Args:
        query (str): The text query to be embedded.

    Returns:
        str: The embedding key generated for the query.
    """
    embedding_result = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=query
    )
    embedding_key = embedding_result['data'][0]["embedding"]
    return embedding_key
