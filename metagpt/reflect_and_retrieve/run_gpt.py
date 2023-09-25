#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : 调用PROMPT
# author: didi
# Date:9.25

import random
import json
from gpt_structure import final_response,prompt_generate

# 使用GPT衡量心酸程度  
def run_gpt_prompt_chat_poignancy(agent,event_description):
    """
    使用GA中的run GPT构造，具体的代码可以参考昨天GPT的内容
    https://chat.openai.com/c/afddac31-300e-427b-9947-4b3ca16bd3a1
    其中输入的ISS是identity stable set
    """
    def create_prompt_input(agent,event_description): 
        prompt_input =  [agent.name,
                        agent.iss,
                        agent.name,
                        event_description]
        return prompt_input

    # 1. Prompt构建
    # 2. Instruction给出
    prompt_template = "Prompt_template/poignancy_chat_v1.txt" ########
    prompt_input = create_prompt_input(agent, event_description)  ########
    prompt = prompt_generate(prompt_input, prompt_template)
    special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."
    poignancy = final_response(prompt,special_instruction)
    try:
        poi_dict = json.loads(poignancy)
        return (poi_dict['poignancy'])
    except:
        return poignancy
    
# 返回John随机记忆
def run_gpt_random_concept():
    random_memories = [
    "Helped Mrs. Moore carry groceries into her house.",
    "Had a friendly chat with Yuriko about her garden.",
    "Met Tom Moreno for coffee during our lunch break.",
    "Talked to Mei about their upcoming vacation plans.",
    "Eddy played his new music composition for me.",
    "Helped a customer find a specific medication.",
    "John divorced his wife because he was in love with someone else",
    "Helped Mrs. Moore carry groceries into her house.",
    "Had a friendly chat with Yuriko about her garden.",
    "Met Tom Moreno for coffee during our lunch break.",
    "Talked to Mei about their upcoming vacation plans.",
    "Eddy played his new music composition for me.",
    "Helped a customer find a specific medication.",
    "Wished Carmen a good day as she passed by the pharmacy.",
    "Discussed local politics with Tom Moreno.",
    "Gave gardening tips to Mrs. Yamamoto.",
    "Saw Jane Moreno jogging in the morning."]
    return(random.choice(random_memories))
