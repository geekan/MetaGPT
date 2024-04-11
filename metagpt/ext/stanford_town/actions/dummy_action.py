#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : dummy action to make every STRole can deal DummyMessage which is caused by DummyAction

from metagpt.actions import Action
from metagpt.schema import Message


class DummyAction(Action):
    async def run(self, *args, **kwargs):
        raise NotImplementedError


class DummyMessage(Message):
    """
    dummy message to pass to role and make them to have a execution every round
    """

    content: str = "dummy"
    cause_by: str = "DummyAction"
