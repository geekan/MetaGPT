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
from metagpt.const import SYSTEM_DESIGN_FILE_REPO, TASK_FILE_REPO
from metagpt.schema import (
    AIMessage,
    CodeSummarizeContext,
    Document,
    Message,
    MessageQueue,
    Plan,
    SystemMessage,
    Task,
    UMLClassAttribute,
    UMLClassMethod,
    UMLClassView,
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
    assert new_message.instruct_content == message.instruct_content  # TODO
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
    attr_a = UMLClassAttribute(name="a", value_type="int", default_value="0", visibility="+")
    assert attr_a.get_mermaid(align=1) == "\t+int a=0"
    attr_b = UMLClassAttribute(name="b", value_type="str", default_value="0", visibility="#")
    assert attr_b.get_mermaid(align=0) == '#str b="0"'
    class_view = UMLClassView(name="A")
    class_view.attributes = [attr_a, attr_b]

    method_a = UMLClassMethod(name="run", visibility="+")
    assert method_a.get_mermaid(align=1) == "\t+run()"
    method_b = UMLClassMethod(
        name="_test",
        visibility="#",
        args=[UMLClassAttribute(name="a", value_type="str"), UMLClassAttribute(name="b", value_type="int")],
        return_type="str",
    )
    assert method_b.get_mermaid(align=0) == "#_test(str a,int b) str"
    class_view.methods = [method_a, method_b]
    assert (
        class_view.get_mermaid(align=0)
        == 'class A{\n\t+int a=0\n\t#str b="0"\n\t+run()\n\t#_test(str a,int b) str\n}\n'
    )


class TestPlan:
    def test_add_tasks_ordering(self):
        plan = Plan(goal="")

        tasks = [
            Task(task_id="1", dependent_task_ids=["2", "3"], instruction="Third"),
            Task(task_id="2", instruction="First"),
            Task(task_id="3", dependent_task_ids=["2"], instruction="Second"),
        ]  # 2 -> 3 -> 1
        plan.add_tasks(tasks)

        assert [task.task_id for task in plan.tasks] == ["2", "3", "1"]

    def test_add_tasks_to_existing_no_common_prefix(self):
        plan = Plan(goal="")

        tasks = [
            Task(task_id="1", dependent_task_ids=["2", "3"], instruction="Third"),
            Task(task_id="2", instruction="First"),
            Task(task_id="3", dependent_task_ids=["2"], instruction="Second", is_finished=True),
        ]  # 2 -> 3 -> 1
        plan.add_tasks(tasks)

        new_tasks = [Task(task_id="3", instruction="")]
        plan.add_tasks(new_tasks)

        assert [task.task_id for task in plan.tasks] == ["3"]
        assert not plan.tasks[0].is_finished  # must be the new unfinished task

    def test_add_tasks_to_existing_with_common_prefix(self):
        plan = Plan(goal="")

        tasks = [
            Task(task_id="1", dependent_task_ids=["2", "3"], instruction="Third"),
            Task(task_id="2", instruction="First"),
            Task(task_id="3", dependent_task_ids=["2"], instruction="Second"),
        ]  # 2 -> 3 -> 1
        plan.add_tasks(tasks)
        plan.finish_current_task()  # finish 2
        plan.finish_current_task()  # finish 3

        new_tasks = [
            Task(task_id="4", dependent_task_ids=["3"], instruction="Third"),
            Task(task_id="2", instruction="First"),
            Task(task_id="3", dependent_task_ids=["2"], instruction="Second"),
        ]  # 2 -> 3 -> 4, so the common prefix is 2 -> 3, and these two should be obtained from the existing tasks
        plan.add_tasks(new_tasks)

        assert [task.task_id for task in plan.tasks] == ["2", "3", "4"]
        assert (
            plan.tasks[0].is_finished and plan.tasks[1].is_finished
        )  # "2" and "3" should be the original finished one
        assert plan.current_task_id == "4"

    def test_current_task(self):
        plan = Plan(goal="")
        tasks = [
            Task(task_id="1", dependent_task_ids=["2"], instruction="Second"),
            Task(task_id="2", instruction="First"),
        ]
        plan.add_tasks(tasks)
        assert plan.current_task.task_id == "2"

    def test_finish_task(self):
        plan = Plan(goal="")
        tasks = [
            Task(task_id="1", instruction="First"),
            Task(task_id="2", dependent_task_ids=["1"], instruction="Second"),
        ]
        plan.add_tasks(tasks)
        plan.finish_current_task()
        assert plan.current_task.task_id == "2"

    def test_finished_tasks(self):
        plan = Plan(goal="")
        tasks = [
            Task(task_id="1", instruction="First"),
            Task(task_id="2", dependent_task_ids=["1"], instruction="Second"),
        ]
        plan.add_tasks(tasks)
        plan.finish_current_task()
        finished_tasks = plan.get_finished_tasks()
        assert len(finished_tasks) == 1
        assert finished_tasks[0].task_id == "1"

    def test_reset_task_existing(self):
        plan = Plan(goal="")
        task = Task(task_id="1", instruction="Do something", code="print('Hello')", result="Hello", finished=True)
        plan.add_tasks([task])
        plan.reset_task("1")
        reset_task = plan.task_map["1"]
        assert reset_task.code == ""
        assert reset_task.result == ""
        assert not reset_task.is_finished

    def test_reset_task_non_existing(self):
        plan = Plan(goal="")
        task = Task(task_id="1", instruction="Do something", code="print('Hello')", result="Hello", finished=True)
        plan.add_tasks([task])
        plan.reset_task("2")  # Task with ID 2 does not exist
        assert "1" in plan.task_map
        assert "2" not in plan.task_map

    def test_replace_task_with_dependents(self):
        plan = Plan(goal="")
        tasks = [
            Task(task_id="1", instruction="First Task", finished=True),
            Task(task_id="2", instruction="Second Task", dependent_task_ids=["1"], finished=True),
        ]
        plan.add_tasks(tasks)
        new_task = Task(task_id="1", instruction="Updated First Task")
        plan.replace_task(new_task)
        assert plan.task_map["1"].instruction == "Updated First Task"
        assert not plan.task_map["2"].is_finished  # Dependent task should be reset
        assert plan.task_map["2"].code == ""
        assert plan.task_map["2"].result == ""

    def test_replace_task_non_existing(self):
        plan = Plan(goal="")
        task = Task(task_id="1", instruction="First Task")
        plan.add_tasks([task])
        new_task = Task(task_id="2", instruction="New Task")
        with pytest.raises(AssertionError):
            plan.replace_task(new_task)  # Task with ID 2 does not exist in plan
        assert "1" in plan.task_map
        assert "2" not in plan.task_map

    def test_append_task_with_valid_dependencies(self):
        plan = Plan(goal="Test")
        existing_task = [Task(task_id="1")]
        plan.add_tasks(existing_task)
        new_task = Task(task_id="2", dependent_task_ids=["1"])
        plan.append_task(new_task)
        assert plan.tasks[-1].task_id == "2"
        assert plan.task_map["2"] == new_task

    def test_append_task_with_invalid_dependencies(self):
        new_task = Task(task_id="2", dependent_task_ids=["3"])
        plan = Plan(goal="Test")
        with pytest.raises(AssertionError):
            plan.append_task(new_task)

    def test_append_task_without_dependencies(self):
        plan = Plan(goal="Test")
        existing_task = [Task(task_id="1")]
        plan.add_tasks(existing_task)

        new_task = Task(task_id="2")
        plan.append_task(new_task)

        assert len(plan.tasks) == 2
        assert plan.current_task_id == "1"

    def test_append_task_updates_current_task(self):
        finished_task = Task(task_id="1", is_finished=True)
        new_task = Task(task_id="2")
        plan = Plan(goal="Test", tasks=[finished_task])
        plan.append_task(new_task)
        assert plan.current_task_id == "2"

    def test_update_current_task(self):
        task1 = Task(task_id="1", is_finished=True)
        task2 = Task(task_id="2")
        plan = Plan(goal="Test", tasks=[task1, task2])
        plan._update_current_task()
        assert plan.current_task_id == "2"


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
