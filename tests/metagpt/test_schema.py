#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/20 10:40
@Author  : alexanderwu
@File    : test_schema.py
@Modified By: mashenquan, 2023-11-1. In line with Chapter 2.2.1 and 2.2.2 of RFC 116, introduce unit tests for
            the utilization of the new feature of `Message` class.
"""

import json

import pytest

from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode
from metagpt.actions.write_code import WriteCode
from metagpt.config import CONFIG
from metagpt.const import SYSTEM_DESIGN_FILE_REPO, TASK_FILE_REPO
from metagpt.schema import (
    AIMessage,
    ClassAttribute,
    ClassMethod,
    ClassView,
    CodeSummarizeContext,
    Document,
    Message,
    MessageQueue,
    SystemMessage,
    UserMessage,
)
from metagpt.utils.common import any_to_str


def test_messages():
    test_content = "test_message"
    msgs = [
        UserMessage(content=test_content),
        SystemMessage(content=test_content),
        AIMessage(content=test_content),
        Message(content=test_content, role="QA"),
    ]
    text = str(msgs)
    roles = ["user", "system", "assistant", "QA"]
    assert all([i in text for i in roles])


def test_message():
    Message("a", role="v1")

    m = Message(content="a", role="v1")
    v = m.dump()
    d = json.loads(v)
    assert d
    assert d.get("content") == "a"
    assert d.get("role") == "v1"
    m.role = "v2"
    v = m.dump()
    assert v
    m = Message.load(v)
    assert m.content == "a"
    assert m.role == "v2"

    m = Message(content="a", role="b", cause_by="c", x="d", send_to="c")
    assert m.content == "a"
    assert m.role == "b"
    assert m.send_to == {"c"}
    assert m.cause_by == "c"
    m.sent_from = "e"
    assert m.sent_from == "e"

    m.cause_by = "Message"
    assert m.cause_by == "Message"
    m.cause_by = Action
    assert m.cause_by == any_to_str(Action)
    m.cause_by = Action()
    assert m.cause_by == any_to_str(Action)
    m.content = "b"
    assert m.content == "b"


def test_routes():
    m = Message(content="a", role="b", cause_by="c", x="d", send_to="c")
    m.send_to = "b"
    assert m.send_to == {"b"}
    m.send_to = {"e", Action}
    assert m.send_to == {"e", any_to_str(Action)}


def test_message_serdeser():
    out_mapping = {"field3": (str, ...), "field4": (list[str], ...)}
    out_data = {"field3": "field3 value3", "field4": ["field4 value1", "field4 value2"]}
    ic_obj = ActionNode.create_model_class("code", out_mapping)

    message = Message(content="code", instruct_content=ic_obj(**out_data), role="engineer", cause_by=WriteCode)
    message_dict = message.model_dump()
    assert message_dict["cause_by"] == "metagpt.actions.write_code.WriteCode"
    assert message_dict["instruct_content"] == {
        "class": "code",
        "mapping": {"field3": "(<class 'str'>, Ellipsis)", "field4": "(list[str], Ellipsis)"},
        "value": {"field3": "field3 value3", "field4": ["field4 value1", "field4 value2"]},
    }
    new_message = Message.model_validate(message_dict)
    assert new_message.content == message.content
    assert new_message.instruct_content.model_dump() == message.instruct_content.model_dump()
    assert new_message.instruct_content != message.instruct_content  # TODO
    assert new_message.cause_by == message.cause_by
    assert new_message.instruct_content.field3 == out_data["field3"]

    message = Message(content="code")
    message_dict = message.model_dump()
    new_message = Message(**message_dict)
    assert new_message.instruct_content is None
    assert new_message.cause_by == "metagpt.actions.add_requirement.UserRequirement"
    assert not Message.load("{")


def test_document():
    doc = Document(root_path="a", filename="b", content="c")
    meta_doc = doc.get_meta()
    assert doc.root_path == meta_doc.root_path
    assert doc.filename == meta_doc.filename
    assert meta_doc.content == ""

    assert doc.full_path == str(CONFIG.git_repo.workdir / doc.root_path / doc.filename)


@pytest.mark.asyncio
async def test_message_queue():
    mq = MessageQueue()
    val = await mq.dump()
    assert val == "[]"
    mq.push(Message(content="1"))
    mq.push(Message(content="2中文测试aaa"))
    msg = mq.pop()
    assert msg.content == "1"

    val = await mq.dump()
    assert val
    new_mq = MessageQueue.load(val)
    assert new_mq.pop_all() == mq.pop_all()


@pytest.mark.parametrize(
    ("file_list", "want"),
    [
        (
            [f"{SYSTEM_DESIGN_FILE_REPO}/a.txt", f"{TASK_FILE_REPO}/b.txt"],
            CodeSummarizeContext(
                design_filename=f"{SYSTEM_DESIGN_FILE_REPO}/a.txt", task_filename=f"{TASK_FILE_REPO}/b.txt"
            ),
        )
    ],
)
def test_CodeSummarizeContext(file_list, want):
    ctx = CodeSummarizeContext.loads(file_list)
    assert ctx == want
    m = {ctx: ctx}
    assert want in m


def test_class_view():
    attr_a = ClassAttribute(name="a", value_type="int", default_value="0", visibility="+", abstraction=True)
    assert attr_a.get_mermaid(align=1) == "\t+int a=0*"
    attr_b = ClassAttribute(name="b", value_type="str", default_value="0", visibility="#", static=True)
    assert attr_b.get_mermaid(align=0) == '#str b="0"$'
    class_view = ClassView(name="A")
    class_view.attributes = [attr_a, attr_b]

    method_a = ClassMethod(name="run", visibility="+", abstraction=True)
    assert method_a.get_mermaid(align=1) == "\t+run()*"
    method_b = ClassMethod(
        name="_test",
        visibility="#",
        static=True,
        args=[ClassAttribute(name="a", value_type="str"), ClassAttribute(name="b", value_type="int")],
        return_type="str",
    )
    assert method_b.get_mermaid(align=0) == "#_test(str a,int b):str$"
    class_view.methods = [method_a, method_b]
    assert (
        class_view.get_mermaid(align=0)
        == 'class A{\n\t+int a=0*\n\t#str b="0"$\n\t+run()*\n\t#_test(str a,int b):str$\n}\n'
    )


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
