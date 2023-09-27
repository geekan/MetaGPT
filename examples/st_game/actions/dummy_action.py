#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : dummy action to make every STRole can deal DummyMessage which is caused by DummyAction

from dataclasses import dataclass

from metagpt.actions import Action
from metagpt.schema import Message


class DummyAction(Action):

    async def run(self, *args, **kwargs):
        raise NotImplementedError


@dataclass
class DummyMessage(Message):
    """
    dummy message to pass to role and make them to have a execution every round
    """

    def __init__(self, content: str = "dummy", cause_by=DummyAction):
        super(DummyMessage, self).__init__(content=content,
                                           cause_by=cause_by)
