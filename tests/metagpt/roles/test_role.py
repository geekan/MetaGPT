#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of Role

from pathlib import Path
import shutil
import pytest

from metagpt.roles.role import Role, RoleReactMode
from metagpt.actions.action import Action
from metagpt.schema import Message
from metagpt.actions.add_requirement import BossRequirement
from metagpt.roles.product_manager import ProductManager

serdes_path = Path(__file__).absolute().parent.joinpath("../../data/serdes_storage")


def test_role_serdes():
    stg_path_prefix = serdes_path.joinpath("team/environment/roles/")
    shutil.rmtree(serdes_path.joinpath("team"), ignore_errors=True)

    pm = ProductManager()
    role_tag = f"{pm.__class__.__name__}_{pm.name}"
    stg_path = stg_path_prefix.joinpath(role_tag)
    pm.serialize(stg_path)
    assert stg_path.joinpath("actions/actions_info.json").exists()

    new_pm = Role.deserialize(stg_path)
    assert new_pm.name == pm.name
    assert len(new_pm.get_memories(1)) == 0


class ActionOK(Action):

    async def run(self, messages: list["Message"]):
        return "ok"


class ActionRaise(Action):

    async def run(self, messages: list["Message"]):
        raise RuntimeError("parse error")


class RoleA(Role):

    def __init__(self,
                 name: str = "RoleA",
                 profile: str = "Role A",
                 goal: str = "",
                 constraints: str = ""):
        super(RoleA, self).__init__(name=name, profile=profile, goal=goal, constraints=constraints)
        self._init_actions([ActionOK, ActionRaise])
        self._watch([BossRequirement])
        self._rc.react_mode = RoleReactMode.BY_ORDER

    async def run(self, message: "Message" = None, stg_path: str = None):
        try:
            await super(RoleA, self).run(message)
        except Exception as exp:
            print("exp ", exp)
            self.serialize(stg_path)


@pytest.mark.asyncio
async def test_role_serdes_interrupt():
    role_a = RoleA()
    shutil.rmtree(serdes_path.joinpath("team"), ignore_errors=True)

    stg_path = serdes_path.joinpath(f"team/environment/roles/{role_a.__class__.__name__}_{role_a.name}")
    await role_a.run(
        message=Message(content="demo", cause_by=BossRequirement),
        stg_path=stg_path
    )
    assert role_a._rc.memory.count() == 2

    assert stg_path.joinpath("actions/todo.json").exists()

    new_role_a: Role = Role.deserialize(stg_path)
    assert new_role_a._rc.state == 1
    await role_a.run(
        message=Message(content="demo", cause_by=BossRequirement),
        stg_path=stg_path
    )

