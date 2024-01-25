#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : LIKE scripts/self_explorer.py in stage=learn & mode=auto self_explore_task stage

from metagpt.actions.action import Action

from examples.andriod_assistant.actions.screenshot_parse_an import SCREENSHOT_PARSE_NODE
from examples.andriod_assistant.prompts.assistant_prompt import screenshot_parse_self_explore_template


class SelfLearn(Action):
    name: str = "SelfLearn"

    async def run(self):
        pass
