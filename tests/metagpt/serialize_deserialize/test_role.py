# -*- coding: utf-8 -*-
# @Date    : 11/23/2023 4:49 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

import shutil

import pytest
from pydantic import BaseModel, SerializeAsAny

from metagpt.actions import WriteCode
from metagpt.actions.add_requirement import UserRequirement
from metagpt.logs import logger
from metagpt.roles.engineer import Engineer
from metagpt.roles.product_manager import ProductManager
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.utils.common import format_trackback_info, read_json_file, write_json_file
from tests.metagpt.serialize_deserialize.test_serdeser_base import (
    ActionOK,
    RoleA,
    RoleB,
    RoleC,
    RoleD,
    serdeser_path,
)


def test_roles(context):
    role_a = RoleA()
    assert len(role_a.rc.watch) == 1
    role_b = RoleB()
    assert len(role_a.rc.watch) == 1
    assert len(role_b.rc.watch) == 1

    role_d = RoleD(actions=[ActionOK()])
    assert len(role_d.actions) == 1


def test_role_subclasses(context):
    """test subclasses of role with same fields in ser&deser"""

    class RoleSubClasses(BaseModel):
        roles: list[SerializeAsAny[Role]] = []

    role_subcls = RoleSubClasses(roles=[RoleA(), RoleB()])
    role_subcls_dict = role_subcls.model_dump()

    new_role_subcls = RoleSubClasses(**role_subcls_dict)
    assert isinstance(new_role_subcls.roles[0], RoleA)
    assert isinstance(new_role_subcls.roles[1], RoleB)


def test_role_serialize(context):
    role = Role()
    ser_role_dict = role.model_dump()
    assert "name" in ser_role_dict
    assert "states" in ser_role_dict
    assert "actions" in ser_role_dict


def test_engineer_serdeser(context):
    role = Engineer()
    ser_role_dict = role.model_dump()
    assert "name" in ser_role_dict
    assert "states" in ser_role_dict
    assert "actions" in ser_role_dict

    new_role = Engineer(**ser_role_dict)
    assert new_role.name == "Alex"
    assert new_role.use_code_review is False
    assert len(new_role.actions) == 1
    assert isinstance(new_role.actions[0], WriteCode)


def test_role_serdeser_save(context):
    shutil.rmtree(serdeser_path.joinpath("team"), ignore_errors=True)

    pm = ProductManager()

    stg_path = serdeser_path.joinpath("team", "environment", "roles", f"{pm.__class__.__name__}_{pm.name}")
    role_path = stg_path.joinpath("role.json")
    write_json_file(role_path, pm.model_dump())

    role_dict = read_json_file(role_path)
    new_pm = ProductManager(**role_dict)
    assert new_pm.name == pm.name
    assert len(new_pm.get_memories(1)) == 0


@pytest.mark.asyncio
async def test_role_serdeser_interrupt(context):
    role_c = RoleC()
    shutil.rmtree(serdeser_path.joinpath("team"), ignore_errors=True)

    stg_path = serdeser_path.joinpath("team", "environment", "roles", f"{role_c.__class__.__name__}_{role_c.name}")
    role_path = stg_path.joinpath("role.json")
    try:
        await role_c.run(with_message=Message(content="demo", cause_by=UserRequirement))
    except Exception:
        logger.error(f"Exception in `role_c.run`, detail: {format_trackback_info()}")
        write_json_file(role_path, role_c.model_dump())

    assert role_c.rc.memory.count() == 1

    role_dict = read_json_file(role_path)
    new_role_c: Role = RoleC(**role_dict)
    assert new_role_c.rc.state == 1

    with pytest.raises(Exception):
        await new_role_c.run(with_message=Message(content="demo", cause_by=UserRequirement))


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
