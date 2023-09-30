#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : 调用Prompts中模板，实现相关Action

from wrapper_prompt import special_response_generate, prompt_generate
from memory.scratch import Scratch
from examples.st_game.memory.agent_memory import BasicMemory
import json


def get_poignancy_action(scratch: Scratch, content: BasicMemory.content) -> str:
    """
    衡量事件心酸度
    """
    def create_prompt_input(scratch, content):
        prompt_input = [scratch.name,
                        scratch.iss,
                        scratch.name,
                        content]
        return prompt_input

    # 1. Prompt构建
    # 2. Instruction给出
    prompt_template = "poignancy_action_v1.txt"  # 保留原来的注释
    prompt_input = create_prompt_input(scratch, content)  # 保留原来的注释
    prompt = prompt_generate(prompt_input, prompt_template)
    special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."
    poignancy = special_response_generate(prompt, special_instruction)
    try:
        poi_dict = json.loads(poignancy)
        return str(poi_dict['poignancy'])  # 将返回值强制转换为字符串
    except json.JSONDecodeError as e:
        return poignancy
    
def get_poignancy_chat(scratch: Scratch, content: BasicMemory.content) -> str:
    """
    衡量会话心酸度
    """
    def create_prompt_input(scratch, content):
        prompt_input = [scratch.name,
                        scratch.iss,
                        scratch.name,
                        content]
        return prompt_input

    # 1. Prompt构建
    # 2. Instruction给出
    prompt_template = "poignancy_chat_v1.txt"  # 保留原来的注释
    prompt_input = create_prompt_input(scratch, content)  # 保留原来的注释
    prompt = prompt_generate(prompt_input, prompt_template)
    special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."
    poignancy = special_response_generate(prompt, special_instruction)
    try:
        poi_dict = json.loads(poignancy)
        return str(poi_dict['poignancy'])  # 将返回值强制转换为字符串
    except json.JSONDecodeError as e:
        return poignancy
