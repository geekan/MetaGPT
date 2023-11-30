#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : base test actions / roles used in unittest

from pydantic import BaseModel, Field
from pathlib import Path

from metagpt.actions.action import Action
from metagpt.roles.role import Role, RoleReactMode
from metagpt.actions.add_requirement import BossRequirement
from metagpt.actions.action_output import ActionOutput


serdeser_path = Path(__file__).absolute().parent.joinpath("../../data/serdeser_storage")


class MockMessage(BaseModel):
    """ to test normal dict without postprocess """
    content: str = ""
    instruct_content: BaseModel = Field(default=None)


class ActionPass(Action):
    name: str = "ActionPass"

    async def run(self, messages: list["Message"]) -> ActionOutput:
        output_mapping = {
            "result": (str, ...)
        }
        pass_class = ActionOutput.create_model_class("pass", output_mapping)
        pass_output = ActionOutput("ActionPass run passed", pass_class(**{"result": "pass result"}))

        return pass_output


class ActionOK(Action):
    name: str = "ActionOK"

    async def run(self, messages: list["Message"]) -> str:
        return "ok"


class ActionRaise(Action):
    name: str = "ActionRaise"

    async def run(self, messages: list["Message"]) -> str:
        raise RuntimeError("parse error in ActionRaise")


class RoleA(Role):

    name: str = Field(default="RoleA")
    profile: str = Field(default="Role A")
    goal: str = "RoleA's goal"
    constraints: str = "RoleA's constraints"

    def __init__(self, **kwargs):
        # super(RoleA, self).__init__(**kwargs)
        super().__init__(**kwargs)
        self._init_actions([ActionPass])
        self._watch([BossRequirement])

    async def run(self, message: "Message" = None):
        await super(RoleA, self).run(message)


class RoleB(Role):
    name: str = Field(default="RoleB")
    profile: str = Field(default="Role B")
    goal: str = "RoleB's goal"
    constraints: str = "RoleB's constraints"

    def __init__(self, **kwargs):
        # super(RoleB, self).__init__(**kwargs)
        super().__init__(**kwargs)
        self._init_actions([ActionOK, ActionRaise])
        self._watch([ActionPass])
        self._rc.react_mode = RoleReactMode.BY_ORDER

    async def run(self, message: "Message" = None):
        await super(RoleB, self).run(message)


class RoleC(Role):
    name: str = Field(default="RoleC")
    profile: str = Field(default="Role C")
    goal: str = "RoleC's goal"
    constraints: str = "RoleC's constraints"

    def __init__(self, **kwargs):
        super(RoleC, self).__init__(**kwargs)
        self._init_actions([ActionOK, ActionRaise])
        self._watch([BossRequirement])
        self._rc.react_mode = RoleReactMode.BY_ORDER

    async def run(self, message: "Message" = None):
        await super(RoleC, self).run(message)
