#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : LIKE scripts/self_explorer.py  self_explore_reflect stage

from metagpt.actions.action import Action

from examples.andriod_assistant.prompts.assistant_prompt import screenshot_parse_self_explore_reflect_template


class SelfLearnReflect(Action):
    name: str = "SelfLearnReflect"

    async def run(self):
        pass
