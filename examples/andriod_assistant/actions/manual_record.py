#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : manual record user interaction in stage=learn & mode=manual, LIKE scripts/step_recorder.py

from metagpt.actions.action import Action


class ManualRecord(Action):
    """do a human operation on the screen with human input"""
    name: str = "ManualRecord"

    async def run(self):
        pass
