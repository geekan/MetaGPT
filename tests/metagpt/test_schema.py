#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/20 10:40
@Author  : alexanderwu
@File    : test_schema.py
"""

from metagpt.schema import AIMessage, Message, SystemMessage, UserMessage
from metagpt.actions.action_output import ActionOutput
from metagpt.actions.write_code import WriteCode
from metagpt.utils.serialize import serialize_general_message, deserialize_general_message


def test_messages():
    test_content = 'test_message'
    msgs = [
        UserMessage(test_content),
        SystemMessage(test_content),
        AIMessage(test_content),
        Message(test_content, role='QA')
    ]
    text = str(msgs)
    roles = ['user', 'system', 'assistant', 'QA']
    assert all([i in text for i in roles])


def test_message_serdeser():
    out_mapping = {"field3": (str, ...), "field4": (list[str], ...)}
    out_data = {"field3": "field3 value3", "field4": ["field4 value1", "field4 value2"]}
    ic_obj = ActionOutput.create_model_class("code", out_mapping)

    message = Message(
        content="code",
        instruct_content=ic_obj(**out_data),
        role="engineer",
        cause_by=WriteCode
    )
    message_dict = serialize_general_message(message)
    assert message_dict["cause_by"] == {"action_class": "WriteCode", "module_name": "metagpt.actions.write_code"}
    assert message_dict["instruct_content"] == {
        "class": "code",
        "mapping": {
            "field3": "(<class 'str'>, Ellipsis)",
            "field4": "(list[str], Ellipsis)"
        },
        "value": {
            "field3": "field3 value3",
            "field4": ["field4 value1", "field4 value2"]
        }
    }

    new_message = deserialize_general_message(message_dict)
    assert new_message.content == message.content
    assert new_message.instruct_content == message.instruct_content
    assert new_message.cause_by == message.cause_by
    assert new_message.instruct_content.field3 == out_data["field3"]

    message = Message(content="code")
    message_dict = serialize_general_message(message)
    new_message = deserialize_general_message(message_dict)
    assert new_message.instruct_content is None
    assert new_message.cause_by == ""
