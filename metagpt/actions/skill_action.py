#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/28
@Author  : mashenquan
@File    : skill_action.py
@Desc    : Call learned skill
"""
from __future__ import annotations

import ast
import importlib
import traceback
from copy import deepcopy
from typing import Dict, Optional

from metagpt.actions import Action
from metagpt.learn.skill_loader import Skill
from metagpt.logs import logger
from metagpt.schema import Message


# TOTEST
class ArgumentsParingAction(Action):
    skill: Skill
    ask: str
    rsp: Optional[Message] = None
    args: Optional[Dict] = None

    @property
    def prompt(self):
        prompt = f"{self.skill.name} function parameters description:\n"
        for k, v in self.skill.arguments.items():
            prompt += f"parameter `{k}`: {v}\n"
        prompt += "\n---\n"
        prompt += "Examples:\n"
        for e in self.skill.examples:
            prompt += f"If want you to do `{e.ask}`, return `{e.answer}` brief and clear.\n"
        prompt += "\n---\n"
        prompt += (
            f"\nRefer to the `{self.skill.name}` function description, and fill in the function parameters according "
            'to the example "I want you to do xx" in the Examples section.'
            f"\nNow I want you to do `{self.ask}`, return function parameters in Examples format above, brief and "
            "clear."
        )
        return prompt

    async def run(self, with_message=None, **kwargs) -> Message:
        prompt = self.prompt
        rsp = await self.llm.aask(
            msg=prompt,
            system_msgs=["You are a function parser.", "You can convert spoken words into function parameters."],
        )
        logger.debug(f"SKILL:{prompt}\n, RESULT:{rsp}")
        self.args = ArgumentsParingAction.parse_arguments(skill_name=self.skill.name, txt=rsp)
        self.rsp = Message(content=rsp, role="assistant", instruct_content=self.args, cause_by=self)
        return self.rsp

    @staticmethod
    def parse_arguments(skill_name, txt) -> dict:
        prefix = skill_name + "("
        if prefix not in txt:
            logger.error(f"{skill_name} not in {txt}")
            return None
        if ")" not in txt:
            logger.error(f"')' not in {txt}")
            return None
        begin_ix = txt.find(prefix)
        end_ix = txt.rfind(")")
        args_txt = txt[begin_ix + len(prefix) : end_ix]
        logger.info(args_txt)
        fake_expression = f"dict({args_txt})"
        parsed_expression = ast.parse(fake_expression, mode="eval")
        args = {}
        for keyword in parsed_expression.body.keywords:
            key = keyword.arg
            value = ast.literal_eval(keyword.value)
            args[key] = value
        return args


class SkillAction(Action):
    skill: Skill
    args: Dict
    rsp: Optional[Message] = None

    async def run(self, with_message=None, **kwargs) -> Message:
        """Run action"""
        options = deepcopy(kwargs)
        if self.args:
            for k in self.args.keys():
                if k in options:
                    options.pop(k)
        try:
            rsp = await self.find_and_call_function(self.skill.name, args=self.args, **options)
            self.rsp = Message(content=rsp, role="assistant", cause_by=self)
        except Exception as e:
            logger.exception(f"{e}, traceback:{traceback.format_exc()}")
            self.rsp = Message(content=f"Error: {e}", role="assistant", cause_by=self)
        return self.rsp

    @staticmethod
    async def find_and_call_function(function_name, args, **kwargs) -> str:
        try:
            module = importlib.import_module("metagpt.learn")
            function = getattr(module, function_name)
            # Invoke function and return result
            result = await function(**args, **kwargs)
            return result
        except (ModuleNotFoundError, AttributeError):
            logger.error(f"{function_name} not found")
            raise ValueError(f"{function_name} not found")
