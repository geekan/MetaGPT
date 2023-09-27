#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : 调用PromptTemplates中模板，实现

from wrapper_prompt import special_response_generate,prompt_generate
from memory.scratch import Scratch
from memory.associative_memory import MemoryBasic
import json

def run_gpt_prompt_chat_poignancy(scratch:Scratch,content:MemoryBasic.content)->str:
    """
    衡量事件心酸度
    """
    def create_prompt_input(scratch,content): 
        prompt_input =  [scratch.name,
                        scratch.iss,
                        scratch.name,
                        content]
        return prompt_input

    # 1. Prompt构建
    # 2. Instruction给出
    prompt_template = "prompt_templates/poignancy_chat_v1.txt" ########
    prompt_input = create_prompt_input(scratch, content)  ########
    prompt = prompt_generate(prompt_input, prompt_template)
    special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."
    poignancy = special_response_generate(prompt,special_instruction)
    try:
        poi_dict = json.loads(poignancy)
        return (poi_dict['poignancy'])
    except:
        return poignancy

