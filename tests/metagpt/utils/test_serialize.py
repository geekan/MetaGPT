#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Desc   : the unittest of serialize
"""

from typing import List

from metagpt.actions import WritePRD
from metagpt.actions.action_node import ActionNode
from metagpt.schema import Message
from metagpt.utils.serialize import (
    actionoutout_schema_to_mapping,
    deserialize_message,
    serialize_message,
)


def test_actionoutout_schema_to_mapping():
    schema = {"title": "test", "type": "object", "properties": {"field": {"title": "field", "type": "string"}}}
    mapping = actionoutout_schema_to_mapping(schema)
    assert mapping["field"] == (str, ...)

    schema = {
        "title": "test",
        "type": "object",
        "properties": {"field": {"title": "field", "type": "array", "items": {"type": "string"}}},
    }
    mapping = actionoutout_schema_to_mapping(schema)
    assert mapping["field"] == (list[str], ...)

    schema = {
        "title": "test",
        "type": "object",
        "properties": {
            "field": {
                "title": "field",
                "type": "array",
                "items": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": [{"type": "string"}, {"type": "string"}],
                },
            }
        },
    }
    mapping = actionoutout_schema_to_mapping(schema)
    assert mapping["field"] == (list[list[str]], ...)

    assert True, True


def test_serialize_and_deserialize_message():
    out_mapping = {"field1": (str, ...), "field2": (List[str], ...)}
    out_data = {"field1": "field1 value", "field2": ["field2 value1", "field2 value2"]}
    ic_obj = ActionNode.create_model_class("prd", out_mapping)

    message = Message(
        content="prd demand", instruct_content=ic_obj(**out_data), role="user", cause_by=WritePRD
    )  # WritePRD as test action

    message_ser = serialize_message(message)

    new_message = deserialize_message(message_ser)
    assert new_message.content == message.content
    assert new_message.cause_by == message.cause_by
    assert new_message.instruct_content.field1 == out_data["field1"]
