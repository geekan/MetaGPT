#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :


from metagpt.actions.action_node import ActionNode
from metagpt.actions.add_requirement import UserRequirement
from metagpt.actions.project_management import WriteTasks
from metagpt.environment import Environment
from metagpt.roles.project_manager import ProjectManager
from metagpt.schema import Message
from metagpt.utils.common import any_to_str, read_json_file, write_json_file
from tests.metagpt.serialize_deserialize.test_serdeser_base import (
    ActionOK,
    ActionRaise,
    RoleC,
    serdeser_path,
)


def test_env_serdeser(context):
    env = Environment(context=context)
    env.publish_message(message=Message(content="test env serialize"))

    ser_env_dict = env.model_dump()
    assert "roles" in ser_env_dict
    assert len(ser_env_dict["roles"]) == 0

    new_env = Environment(**ser_env_dict, context=context)
    assert len(new_env.roles) == 0
    assert len(new_env.history) == 25


def test_environment_serdeser(context):
    out_mapping = {"field1": (list[str], ...)}
    out_data = {"field1": ["field1 value1", "field1 value2"]}
    ic_obj = ActionNode.create_model_class("prd", out_mapping)

    message = Message(
        content="prd", instruct_content=ic_obj(**out_data), role="product manager", cause_by=any_to_str(UserRequirement)
    )

    environment = Environment(context=context)
    role_c = RoleC()
    environment.add_role(role_c)
    environment.publish_message(message)

    ser_data = environment.model_dump()
    assert ser_data["roles"]["Role C"]["name"] == "RoleC"

    new_env: Environment = Environment(**ser_data, context=context)
    assert len(new_env.roles) == 1

    assert list(new_env.roles.values())[0].states == list(environment.roles.values())[0].states
    assert isinstance(list(environment.roles.values())[0].actions[0], ActionOK)
    assert type(list(new_env.roles.values())[0].actions[0]) == ActionOK
    assert type(list(new_env.roles.values())[0].actions[1]) == ActionRaise


def test_environment_serdeser_v2(context):
    environment = Environment(context=context)
    pm = ProjectManager()
    environment.add_role(pm)

    ser_data = environment.model_dump()

    new_env: Environment = Environment(**ser_data, context=context)
    role = new_env.get_role(pm.profile)
    assert isinstance(role, ProjectManager)
    assert isinstance(role.actions[0], WriteTasks)
    assert isinstance(list(new_env.roles.values())[0].actions[0], WriteTasks)


def test_environment_serdeser_save(context):
    environment = Environment(context=context)
    role_c = RoleC()

    stg_path = serdeser_path.joinpath("team", "environment")
    env_path = stg_path.joinpath("env.json")
    environment.add_role(role_c)

    write_json_file(env_path, environment.model_dump())

    env_dict = read_json_file(env_path)
    new_env: Environment = Environment(**env_dict, context=context)
    assert len(new_env.roles) == 1
    assert type(list(new_env.roles.values())[0].actions[0]) == ActionOK
