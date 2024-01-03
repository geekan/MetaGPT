# -*- coding: utf-8 -*-
# @Date    : 11/23/2023 4:49 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

import shutil

import pytest
from pydantic import BaseModel, SerializeAsAny

from metagpt.actions import WriteCode
from metagpt.actions.add_requirement import UserRequirement
from metagpt.const import SERDESER_PATH
from metagpt.logs import logger
from metagpt.roles.engineer import Engineer
from metagpt.roles.product_manager import ProductManager
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.utils.common import format_trackback_info
from tests.metagpt.serialize_deserialize.test_serdeser_base import (
    ActionOK,
    RoleA,
    RoleB,
    RoleC,
    RoleD,
    serdeser_path,
)


def test_roles():
    role_a = RoleA()
    assert len(role_a.rc.watch) == 1
    role_b = RoleB()
    assert len(role_a.rc.watch) == 1
    assert len(role_b.rc.watch) == 1

    role_d = RoleD(actions=[ActionOK()])
    assert len(role_d.actions) == 1


def test_role_subclasses():
    """test subclasses of role with same fields in ser&deser"""

    class RoleSubClasses(BaseModel):
        roles: list[SerializeAsAny[Role]] = []

    role_subcls = RoleSubClasses(roles=[RoleA(), RoleB()])
    role_subcls_dict = role_subcls.model_dump()

    new_role_subcls = RoleSubClasses(**role_subcls_dict)
    assert isinstance(new_role_subcls.roles[0], RoleA)
    assert isinstance(new_role_subcls.roles[1], RoleB)


def test_role_serialize():
    role = Role()
    ser_role_dict = role.model_dump()
    assert "name" in ser_role_dict
    assert "states" in ser_role_dict
    assert "actions" in ser_role_dict


def test_engineer_serialize():
    role = Engineer()
    ser_role_dict = role.model_dump()
    assert "name" in ser_role_dict
    assert "states" in ser_role_dict
    assert "actions" in ser_role_dict


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_engineer_deserialize():
    role = Engineer(use_code_review=True)
    ser_role_dict = role.model_dump()

    new_role = Engineer(**ser_role_dict)
    assert new_role.name == "Alex"
    assert new_role.use_code_review is True
    assert len(new_role.actions) == 1
    assert isinstance(new_role.actions[0], WriteCode)
    # await new_role.actions[0].run(context="write a cli snake game", filename="test_code")


def test_role_serdeser_save():
    stg_path_prefix = serdeser_path.joinpath("team", "environment", "roles")
    shutil.rmtree(serdeser_path.joinpath("team"), ignore_errors=True)

    pm = ProductManager()
    role_tag = f"{pm.__class__.__name__}_{pm.name}"
    stg_path = stg_path_prefix.joinpath(role_tag)
    pm.serialize(stg_path)

    new_pm = Role.deserialize(stg_path)
    assert new_pm.name == pm.name
    assert len(new_pm.get_memories(1)) == 0


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_role_serdeser_interrupt():
    role_c = RoleC()
    shutil.rmtree(SERDESER_PATH.joinpath("team"), ignore_errors=True)

    stg_path = SERDESER_PATH.joinpath("team", "environment", "roles", f"{role_c.__class__.__name__}_{role_c.name}")
    try:
        await role_c.run(with_message=Message(content="demo", cause_by=UserRequirement))
    except Exception:
        logger.error(f"Exception in `role_a.run`, detail: {format_trackback_info()}")
        role_c.serialize(stg_path)

    assert role_c.rc.memory.count() == 1

    new_role_a: Role = Role.deserialize(stg_path)
    assert new_role_a.rc.state == 1

    with pytest.raises(Exception):
        await new_role_a.run(with_message=Message(content="demo", cause_by=UserRequirement))


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
