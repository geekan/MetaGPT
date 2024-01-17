#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of memory

from pydantic import BaseModel

from metagpt.actions.action_node import ActionNode
from metagpt.actions.add_requirement import UserRequirement
from metagpt.actions.design_api import WriteDesign
from metagpt.memory.memory import Memory
from metagpt.schema import Message
from metagpt.utils.common import any_to_str, read_json_file, write_json_file
from tests.metagpt.serialize_deserialize.test_serdeser_base import serdeser_path


def test_memory_serdeser(context):
    msg1 = Message(role="Boss", content="write a snake game", cause_by=UserRequirement)

    out_mapping = {"field2": (list[str], ...)}
    out_data = {"field2": ["field2 value1", "field2 value2"]}
    ic_obj = ActionNode.create_model_class("system_design", out_mapping)
    msg2 = Message(
        role="Architect", instruct_content=ic_obj(**out_data), content="system design content", cause_by=WriteDesign
    )

    memory = Memory()
    memory.add_batch([msg1, msg2])
    ser_data = memory.model_dump()

    new_memory = Memory(**ser_data)
    assert new_memory.count() == 2
    new_msg2 = new_memory.get(2)[0]
    assert isinstance(new_msg2, BaseModel)
    assert isinstance(new_memory.storage[-1], BaseModel)
    assert new_memory.storage[-1].cause_by == any_to_str(WriteDesign)
    assert new_msg2.role == "Boss"

    memory = Memory(storage=[msg1, msg2], index={msg1.cause_by: [msg1], msg2.cause_by: [msg2]})
    assert memory.count() == 2


def test_memory_serdeser_save(context):
    msg1 = Message(role="User", content="write a 2048 game", cause_by=UserRequirement)

    out_mapping = {"field1": (list[str], ...)}
    out_data = {"field1": ["field1 value1", "field1 value2"]}
    ic_obj = ActionNode.create_model_class("system_design", out_mapping)
    msg2 = Message(
        role="Architect", instruct_content=ic_obj(**out_data), content="system design content", cause_by=WriteDesign
    )

    memory = Memory()
    memory.add_batch([msg1, msg2])

    stg_path = serdeser_path.joinpath("team", "environment")
    memory_path = stg_path.joinpath("memory.json")
    write_json_file(memory_path, memory.model_dump())
    assert memory_path.exists()

    memory_dict = read_json_file(memory_path)
    new_memory = Memory(**memory_dict)
    assert new_memory.count() == 2
    new_msg2 = new_memory.get(1)[0]
    assert new_msg2.instruct_content.field1 == ["field1 value1", "field1 value2"]
    assert new_msg2.cause_by == any_to_str(WriteDesign)
    assert len(new_memory.index) == 2
