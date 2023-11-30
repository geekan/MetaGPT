# -*- coding: utf-8 -*-
# @Date    : 11/23/2023 4:49 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

from pathlib import Path
import shutil
import pytest

from metagpt.logs import logger
from metagpt.roles.role import Role
from metagpt.actions import WriteCode, WriteCodeReview
from metagpt.schema import Message
from metagpt.actions.add_requirement import BossRequirement
from metagpt.roles.product_manager import ProductManager
from metagpt.const import SERDESER_PATH
from metagpt.roles.engineer import Engineer
from metagpt.utils.utils import format_trackback_info

from tests.metagpt.serialize_deserialize.test_serdeser_base import RoleA, RoleB, RoleC, serdeser_path


def test_roles():
    role_a = RoleA()
    assert len(role_a._rc.watch) == 1
    role_b = RoleB()
    assert len(role_a._rc.watch) == 1
    assert len(role_b._rc.watch) == 1


def test_role_serialize():
    role = Role()
    ser_role_dict = role.dict(by_alias=True)
    assert "name" in ser_role_dict
    assert "_states" in ser_role_dict
    assert "_actions" in ser_role_dict


def test_engineer_serialize():
    role = Engineer()
    ser_role_dict = role.dict(by_alias=True)
    assert "name" in ser_role_dict
    assert "_states" in ser_role_dict
    assert "_actions" in ser_role_dict


@pytest.mark.asyncio
async def test_engineer_deserialize():
    role = Engineer(use_code_review=True)
    ser_role_dict = role.dict(by_alias=True)

    new_role = Engineer(**ser_role_dict)
    assert new_role.name == "Alex"
    assert new_role.use_code_review is True
    assert len(new_role._actions) == 2
    assert isinstance(new_role._actions[0], WriteCode)
    assert isinstance(new_role._actions[1], WriteCodeReview)
    # await new_role._actions[0].run(context="write a cli snake game", filename="test_code")


def test_role_serdeser_save():
    stg_path_prefix = serdeser_path.joinpath("team/environment/roles/")
    shutil.rmtree(serdeser_path.joinpath("team"), ignore_errors=True)

    pm = ProductManager()
    role_tag = f"{pm.__class__.__name__}_{pm.name}"
    stg_path = stg_path_prefix.joinpath(role_tag)
    pm.serialize(stg_path)
    assert stg_path.joinpath("actions/actions_info.json").exists()

    new_pm = Role.deserialize(stg_path)
    assert new_pm.name == pm.name
    assert len(new_pm.get_memories(1)) == 0


@pytest.mark.asyncio
async def test_role_serdeser_interrupt():
    role_c = RoleC()
    shutil.rmtree(SERDESER_PATH.joinpath("team"), ignore_errors=True)

    stg_path = SERDESER_PATH.joinpath(f"team/environment/roles/{role_c.__class__.__name__}_{role_c.name}")
    try:
        await role_c.run(
            message=Message(content="demo", cause_by=BossRequirement)
        )
    except Exception as exp:
        logger.error(f"Exception in `role_a.run`, detail: {format_trackback_info()}")
        role_c.serialize(stg_path)

    assert role_c._rc.memory.count() == 2

    assert stg_path.joinpath("actions/todo.json").exists()

    new_role_a: Role = Role.deserialize(stg_path)
    assert new_role_a._rc.state == 1

    with pytest.raises(Exception):
        await role_c.run(
            message=Message(content="demo", cause_by=BossRequirement)
        )
