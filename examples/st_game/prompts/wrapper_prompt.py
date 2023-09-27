#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : 基于Prmopt Templates 填充Prompt; 为Prompt包装与调用

from metagpt import llm

def prompt_generate(curr_input:list, prompt_path:str):
    """
    curr_input:输入一个按照PromptTemplate的要求的列表
    prompt_path:输入一个Promptpath
    """
    if type(curr_input) == type("string"): 
        curr_input = [curr_input]
        curr_input = [str(i) for i in curr_input]

    f = open(prompt_path, "r")
    prompt = f.read()
    f.close()
    for count, i in enumerate(curr_input):   
        prompt = prompt.replace(f"!<INPUT {count}>!", i)
    if "<commentblockmarker>###</commentblockmarker>" in prompt: 
        prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
    return prompt.strip()

def response_generate(prompt:str):
    """
    待完善，我没有找到MG中可以设置Temprature以及Maxtoken的位置
    """
    return llm.ai_func(prompt)

def special_response_generate(prompt:str,special_instruction:str,example_output:str = None):
    """
    当对于Prompt生成有特殊要求时，调用该函数增加special_instruction或example_output
    """
    prompt = '"""\n' + prompt + '\n"""\n'
    prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
    if example_output:    
        prompt += "Example output json:\n"
        prompt += '{"output": "' + str(example_output) + '"}'
    return response_generate(prompt)


