#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/15 15:00
@Author  : mczhuge
@File    : handover_eval.py
"""
import os
import json
from typing import List, Tuple
from metagpt.actions import Action, ActionOutput
from metagpt.actions.search_and_summarize import SearchAndSummarize
from metagpt.logs import logger
from metagpt.config import CONFIG

ROSTER = {
    "BOSS": {"name": "BOSS", "next": "ProductManager"},
    "ProductManager": {"name": "Alice", "next": "Architect"},
    "Architect": {"name": "Bob", "next": "ProjectManager"},
    "ProjectManager": {"name": "Eve", "next": "Engineer"},
    "Engineer": {"name": "Alex", "next": "QaEngineer"},
    "QaEngineer": {"name": "Edward", "next": None},
}

def print_with_color(text, color="red"):

    color_codes = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
    }
    print(f"{color_codes[color]}  {text} {color_codes['reset']}")



class Feedback(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

        # Noted: Using 'They' or 'Their' is not a grammatical issue; https://www.quora.com/What-pronoun-to-use-when-you-dont-know-the-gender
        self.PROMPT_TEMPLATE = """You are {your_name}, in the role of {your_role}. 
            You recently worked together with {prev_name} on a project, where they held the position of {prev_role}. 
            They shared their work details with you: {prev_msg}. 
            Your current task involves incorporating their input into your {your_role} duties. 
            Evaluate this handover process critically and suggest potential ways for improvement, as if you were analyzing a real work situation. 
            Please provide your assessment concisely in 30 words or less:
            """


    async def run(self, handover_msg, *args, **kwargs) -> ActionOutput:

        #prev_role = handover_msg[0].to_dict()["role"]
        #prev_msg = handover_msg[0].to_dict()["content"]
        if  isinstance(handover_msg, list):
            handover_msg = handover_msg[0]
        prev_role = handover_msg.to_dict()["role"].replace(" ", "")
        prev_msg = handover_msg.to_dict()["content"]

        prev_name = ROSTER[prev_role]["name"]
        your_role = ROSTER[prev_role]["next"]
        your_name = ROSTER[your_role]["name"]

        prompt = self.PROMPT_TEMPLATE.format(your_name=your_name,
                                             your_role=your_role,
                                             prev_name=prev_name,
                                             prev_role=prev_role,
                                             prev_msg=prev_msg)
        logger.debug(prompt)
        feedback = await self._aask(prompt)

        handover_record = CONFIG.handover_file
        # if os.path.exists(handover_record):
        #     with open(handover_record, "r+") as file:
        #         data = json.load(file)
        # else: data = {}

        # data["new_key"] = "new_value"
        # with open(handover_record, "w") as file:
        #     json.dump(data, file)

        return feedback
