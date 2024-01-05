#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of schema ser&deser

from metagpt.actions.action_node import ActionNode
from metagpt.actions.write_code import WriteCode
from metagpt.schema import Document, Documents, Message
from metagpt.utils.common import any_to_str
from tests.metagpt.serialize_deserialize.test_serdeser_base import (
    MockICMessage,
    MockMessage,
)


def test_message_serdeser():
    out_mapping = {"field3": (str, ...), "field4": (list[str], ...)}
    out_data = {"field3": "field3 value3", "field4": ["field4 value1", "field4 value2"]}
    ic_obj = ActionNode.create_model_class("code", out_mapping)

    message = Message(content="code", instruct_content=ic_obj(**out_data), role="engineer", cause_by=WriteCode)
    ser_data = message.model_dump()
    assert ser_data["cause_by"] == "metagpt.actions.write_code.WriteCode"
    assert ser_data["instruct_content"]["class"] == "code"

    new_message = Message(**ser_data)
    assert new_message.cause_by == any_to_str(WriteCode)
    assert new_message.cause_by in [any_to_str(WriteCode)]
    assert new_message.instruct_content != ic_obj(**out_data)  # TODO find why `!=`
    assert new_message.instruct_content.model_dump() == ic_obj(**out_data).model_dump()

    message = Message(content="test_ic", instruct_content=MockICMessage())
    ser_data = message.model_dump()
    new_message = Message(**ser_data)
    assert new_message.instruct_content != MockICMessage()  # TODO

    message = Message(content="test_documents", instruct_content=Documents(docs={"doc1": Document(content="test doc")}))
    ser_data = message.model_dump()
    assert "class" in ser_data["instruct_content"]


def test_message_without_postprocess():
    """to explain `instruct_content` should be postprocessed"""
    out_mapping = {"field1": (list[str], ...)}
    out_data = {"field1": ["field1 value1", "field1 value2"]}
    ic_obj = ActionNode.create_model_class("code", out_mapping)
    message = MockMessage(content="code", instruct_content=ic_obj(**out_data))
    ser_data = message.model_dump()
    assert ser_data["instruct_content"] == {}

    ser_data["instruct_content"] = None
    new_message = MockMessage(**ser_data)
    assert new_message.instruct_content != ic_obj(**out_data)
