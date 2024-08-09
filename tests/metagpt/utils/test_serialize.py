#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Desc   : the unittest of serialize
"""

from typing import List

from pydantic import BaseModel

from metagpt.actions import WritePRD
from metagpt.actions.action_node import ActionNode
from metagpt.schema import Message
from metagpt.utils.serialize import (
    actionoutout_schema_to_mapping,
    deserialize_message,
    deserialize_model,
    serialize_message,
    serialize_model,
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


class TestUserModel(BaseModel):
    name: str
    value: int


def test_serialize_model(mocker):
    model = TestUserModel(name="test", value=42)
    file_path = "test.json"
    mock_write_json_file = mocker.patch("metagpt.utils.serialize.write_json_file")

    # Test without remove_unserializable
    serialize_model(model, file_path)
    mock_write_json_file.assert_called_once_with(file_path, model.model_dump())

    # Test with remove_unserializable
    def remove_unserializable(data: dict):
        data.pop("value", None)

    serialize_model(model, file_path, remove_unserializable)
    mock_write_json_file.assert_called_with(file_path, {"name": "test"})


def test_deserialize_model(mocker):
    file_path = "test.json"
    data = {"name": "test", "value": 42}
    mock_read_json_file = mocker.patch("metagpt.utils.serialize.read_json_file", return_value=data)

    model = deserialize_model(TestUserModel, file_path)
    mock_read_json_file.assert_called_once_with(file_path)
    assert model == TestUserModel(**data)
