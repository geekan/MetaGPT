#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : base test actions / roles used in unittest

import asyncio
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from metagpt.actions import Action, ActionOutput
from metagpt.actions.action_node import ActionNode
from metagpt.actions.add_requirement import UserRequirement
from metagpt.roles.role import Role, RoleReactMode

serdeser_path = Path(__file__).absolute().parent.joinpath("..", "..", "data", "serdeser_storage")


class MockMessage(BaseModel):
    content: str = "test_msg"


class MockICMessage(BaseModel):
    """to test normal dict without postprocess"""

    content: str = "test_ic_msg"
    instruct_content: Optional[BaseModel] = Field(default=None)


class ActionPass(Action):
    name: str = "ActionPass"

    async def run(self, messages: list["Message"]) -> ActionOutput:
        await asyncio.sleep(5)  # sleep to make other roles can watch the executed Message
        output_mapping = {"result": (str, ...)}
        pass_class = ActionNode.create_model_class("pass", output_mapping)
        pass_output = ActionOutput("ActionPass run passed", pass_class(**{"result": "pass result"}))

        return pass_output


class ActionOK(Action):
    name: str = "ActionOK"

    async def run(self, messages: list["Message"]) -> str:
        await asyncio.sleep(5)
        return "ok"


class ActionRaise(Action):
    name: str = "ActionRaise"

    async def run(self, messages: list["Message"]) -> str:
        raise RuntimeError("parse error in ActionRaise")


class ActionOKV2(Action):
    name: str = "ActionOKV2"
    extra_field: str = "ActionOKV2 Extra Info"


class RoleA(Role):
    name: str = Field(default="RoleA")
    profile: str = Field(default="Role A")
    goal: str = "RoleA's goal"
    constraints: str = "RoleA's constraints"

    def __init__(self, **kwargs):
        super(RoleA, self).__init__(**kwargs)
        self.set_actions([ActionPass])
        self._watch([UserRequirement])


class RoleB(Role):
    name: str = Field(default="RoleB")
    profile: str = Field(default="Role B")
    goal: str = "RoleB's goal"
    constraints: str = "RoleB's constraints"

    def __init__(self, **kwargs):
        super(RoleB, self).__init__(**kwargs)
        self.set_actions([ActionOK, ActionRaise])
        self._watch([ActionPass])
        self.rc.react_mode = RoleReactMode.BY_ORDER


class RoleC(Role):
    name: str = Field(default="RoleC")
    profile: str = Field(default="Role C")
    goal: str = "RoleC's goal"
    constraints: str = "RoleC's constraints"

    def __init__(self, **kwargs):
        super(RoleC, self).__init__(**kwargs)
        self.set_actions([ActionOK, ActionRaise])
        self._watch([UserRequirement])
        self.rc.react_mode = RoleReactMode.BY_ORDER
        self.rc.memory.ignore_id = True


class RoleD(Role):
    name: str = Field(default="RoleD")
    profile: str = Field(default="Role D")
    goal: str = "RoleD's goal"
    constraints: str = "RoleD's constraints"
