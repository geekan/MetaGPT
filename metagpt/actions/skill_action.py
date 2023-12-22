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

from metagpt.actions import Action, ActionOutput
from metagpt.learn.skill_loader import Skill
from metagpt.logs import logger


class ArgumentsParingAction(Action):
    skill: Skill
    ask: str
    rsp: Optional[ActionOutput]
    args: Optional[Dict]

    @property
    def prompt(self):
        prompt = f"{self.skill.name} function parameters description:\n"
        for k, v in self.skill.arguments.items():
            prompt += f"parameter `{k}`: {v}\n"
        prompt += "\n"
        prompt += "Examples:\n"
        for e in self.skill.examples:
            prompt += f"If want you to do `{e.ask}`, return `{e.answer}` brief and clear.\n"
        prompt += f"\nNow I want you to do `{self.ask}`, return in examples format above, brief and clear."
        return prompt

    async def run(self, *args, **kwargs) -> ActionOutput:
        prompt = self.prompt
        rsp = await self.llm.aask(msg=prompt, system_msgs=[])
        logger.debug(f"SKILL:{prompt}\n, RESULT:{rsp}")
        self.args = ArgumentsParingAction.parse_arguments(skill_name=self.skill.name, txt=rsp)
        self.rsp = ActionOutput(content=rsp)
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
    rsp: str = ""

    async def run(self, *args, **kwargs) -> str | ActionOutput | None:
        """Run action"""
        options = deepcopy(kwargs)
        if self.args:
            for k in self.args.keys():
                if k in options:
                    options.pop(k)
        try:
            self.rsp = await self.find_and_call_function(self.skill.name, args=self.args, **options)
        except Exception as e:
            logger.exception(f"{e}, traceback:{traceback.format_exc()}")
            self.rsp = f"Error: {e}"
        return ActionOutput(content=self.rsp, instruct_content=self.skill.json())

    @staticmethod
    async def find_and_call_function(function_name, args, **kwargs):
        try:
            module = importlib.import_module("metagpt.learn")
            function = getattr(module, function_name)
            # 调用函数并返回结果
            result = await function(**args, **kwargs)
            return result
        except (ModuleNotFoundError, AttributeError):
            logger.error(f"{function_name} not found")
            return None


if __name__ == "__main__":
    ArgumentsParingAction.parse_arguments(
        skill_name="text_to_image", txt='`text_to_image(text="Draw an apple", size_type="512x512")`'
    )
