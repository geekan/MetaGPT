#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of schema ser&deser
import pytest

from metagpt.actions.action_node import ActionNode
from metagpt.actions.write_code import WriteCode
from metagpt.schema import CodingContext, Document, Documents, Message, TestingContext
from metagpt.utils.common import any_to_str
from tests.metagpt.serialize_deserialize.test_serdeser_base import (
    MockICMessage,
    MockMessage,
)


def test_message_serdeser_from_create_model():
    with pytest.raises(KeyError):
        _ = Message(content="code", instruct_content={"class": "test", "key": "value"})

    out_mapping = {"field3": (str, ...), "field4": (list[str], ...)}
    out_data = {"field3": "field3 value3", "field4": ["field4 value1", "field4 value2"]}
    ic_obj = ActionNode.create_model_class("code", out_mapping)
    ic_inst = ic_obj(**out_data)

    message = Message(content="code", instruct_content=ic_inst, role="engineer", cause_by=WriteCode)
    ser_data = message.model_dump()
    assert ser_data["cause_by"] == "metagpt.actions.write_code.WriteCode"
    assert ser_data["instruct_content"]["class"] == "code"

    new_message = Message(**ser_data)
    assert new_message.cause_by == any_to_str(WriteCode)
    assert new_message.cause_by in [any_to_str(WriteCode)]

    assert new_message.instruct_content == ic_obj(**out_data)
    assert new_message.instruct_content == ic_inst
    assert new_message.instruct_content.model_dump() == ic_obj(**out_data).model_dump()
    assert new_message == message

    mock_msg = MockMessage()
    message = Message(content="test_ic", instruct_content=mock_msg)
    ser_data = message.model_dump()
    new_message = Message(**ser_data)
    assert new_message.instruct_content == mock_msg
    assert new_message == message


def test_message_without_postprocess():
    """to explain `instruct_content` from `create_model_class` should be postprocessed"""
    out_mapping = {"field1": (list[str], ...)}
    out_data = {"field1": ["field1 value1", "field1 value2"]}
    ic_obj = ActionNode.create_model_class("code", out_mapping)
    message = MockICMessage(content="code", instruct_content=ic_obj(**out_data))
    ser_data = message.model_dump()
    assert ser_data["instruct_content"] == {}

    ser_data["instruct_content"] = None
    new_message = MockICMessage(**ser_data)
    assert new_message.instruct_content != ic_obj(**out_data)
    assert new_message != message


def test_message_serdeser_from_basecontext():
    doc_msg = Message(content="test_document", instruct_content=Document(content="test doc"))
    ser_data = doc_msg.model_dump()
    assert ser_data["instruct_content"]["value"]["content"] == "test doc"
    assert ser_data["instruct_content"]["value"]["filename"] == ""

    docs_msg = Message(
        content="test_documents", instruct_content=Documents(docs={"doc1": Document(content="test doc")})
    )
    ser_data = docs_msg.model_dump()
    assert ser_data["instruct_content"]["class"] == "Documents"
    assert ser_data["instruct_content"]["value"]["docs"]["doc1"]["content"] == "test doc"
    assert ser_data["instruct_content"]["value"]["docs"]["doc1"]["filename"] == ""

    code_ctxt = CodingContext(
        filename="game.py",
        design_doc=Document(root_path="docs/system_design", filename="xx.json", content="xxx"),
        task_doc=Document(root_path="docs/tasks", filename="xx.json", content="xxx"),
        code_doc=Document(root_path="xxx", filename="game.py", content="xxx"),
    )
    code_ctxt_msg = Message(content="coding_context", instruct_content=code_ctxt)
    ser_data = code_ctxt_msg.model_dump()
    assert ser_data["instruct_content"]["class"] == "CodingContext"

    new_code_ctxt_msg = Message(**ser_data)
    assert new_code_ctxt_msg.instruct_content == code_ctxt
    assert new_code_ctxt_msg.instruct_content.code_doc.filename == "game.py"
    assert new_code_ctxt_msg == code_ctxt_msg

    testing_ctxt = TestingContext(
        filename="test.py",
        code_doc=Document(root_path="xxx", filename="game.py", content="xxx"),
        test_doc=Document(root_path="docs/tests", filename="test.py", content="xxx"),
    )
    testing_ctxt_msg = Message(content="testing_context", instruct_content=testing_ctxt)
    ser_data = testing_ctxt_msg.model_dump()
    new_testing_ctxt_msg = Message(**ser_data)
    assert new_testing_ctxt_msg.instruct_content == testing_ctxt
    assert new_testing_ctxt_msg.instruct_content.test_doc.filename == "test.py"
    assert new_testing_ctxt_msg == testing_ctxt_msg
