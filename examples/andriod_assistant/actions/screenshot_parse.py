#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : LIKE scripts/task_executor.py in stage=act

from metagpt.actions.action import Action


class ScreenshotParse(Action):
    name: str = "ScreenshotParse"

    async def run(self):
        pass
