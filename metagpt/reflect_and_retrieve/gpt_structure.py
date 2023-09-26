#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : 调用GPT
# author: didi
# Date:9.25

import openai
openai.api_key = "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"
openai.proxy = 'http://127.0.0.1:7000'
# 直接调用Prompt生成


def response_generate(prompt):
    """
    通过将特殊指令加入Prompt生成最终的响应。

    参数：
    - prompt：要生成响应的提示文本。
    - special_instruction：要加入Prompt的特殊指令。
    - example_output（可选）：示例输出的JSON字符串。

    返回：
    生成的最终响应。

    """
    completion = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        temperature=0,
        max_tokens=500,
        top_p=1,
        stream=False,
        frequency_penalty=0,
        presence_penalty=0
    )
    return (completion.choices[0].text)

# 特殊指令加入Prompt生成


def final_response(prompt, special_instruction, example_output=None):
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
    return response_generate(prompt)

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
    if type(curr_input) == type("string"):
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
