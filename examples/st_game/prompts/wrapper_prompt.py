#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : 基于Prompt Templates 填充Prompt; 为Prompt包装与调用

from metagpt import llm


def prompt_generate(curr_input: list, prompt_path: str):
    """
    curr_input: 输入一个按照Prompt Template的要求的列表
    prompt_path: 输入一个Prompt path
    """
    # 如果输入是字符串，将其转换为列表
    if isinstance(curr_input, str):
        curr_input = [curr_input]

    # 将输入列表中的每个元素转换为字符串
    curr_input = [str(i) for i in curr_input]

    with open(prompt_path, "r") as f:
        prompt = f.read()

    for count, i in enumerate(curr_input):
        prompt = prompt.replace(f"!<INPUT {count}>!", i)

    if "<commentblockmarker>###</commentblockmarker>" in prompt:
        prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]

    return prompt.strip()


def response_generate(prompt: str):
    """
    待完善，我没有找到MG中可以设置Temperature以及Maxtoken的位置
    """
    return llm.ai_func(prompt)


def special_response_generate(prompt: str, special_instruction: str, example_output: str = None):
    """
    当对于Prompt生成有特殊要求时，调用该函数增加special_instruction或example_output
    """
    prompt = '"""\n' + prompt + '\n"""\n'
    prompt += f"Output the response to the prompt above in JSON. {special_instruction}\n"

    if example_output:
        prompt += "Example output JSON:\n"
        prompt += '{"output": "' + str(example_output) + '"}'

    return response_generate(prompt)
