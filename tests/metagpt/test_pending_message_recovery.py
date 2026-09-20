"""Pending receive queues must survive Team checkpoints (#2151)."""

import json

import pytest

from metagpt.ext.werewolf.schema import WwMessage
from metagpt.memory import Memory
from metagpt.roles.project_manager import ProjectManager
from metagpt.roles.role import Role
from metagpt.schema import AIMessage, Document, Message, MessageQueue, UserMessage
from metagpt.team import Team


def test_message_queue_model_round_trip():
    messages = [
        Message(content="first", send_to={"A", "B"}, instruct_content=Document(content="payload")),
        Message(content="second"),
    ]
    queue = MessageQueue()
    for message in messages:
        queue.push(message)

    assert MessageQueue.model_validate(queue) is queue
    restored = MessageQueue.model_validate_json(queue.model_dump_json())
    assert restored.pop_all() == messages
    assert queue.pop_all() == messages
    assert MessageQueue.model_validate({}).empty()


@pytest.mark.asyncio
@pytest.mark.parametrize("role_class", [Role, ProjectManager])
@pytest.mark.parametrize("message_count", [0, 1, 3])
async def test_pending_messages_survive_recovery(tmp_path, message_count, role_class):
    role = role_class(name="receiver", profile="receiver")
    team = Team(use_mgx=False, roles=[role])
    messages = [Message(content=f"pending {index}", send_to=role.name) for index in range(message_count)]
    for message in messages:
        role.put_message(message)

    team.serialize(tmp_path)
    team.serialize(tmp_path)
    assert role.rc.msg_buffer.pop_all() == messages
    assert role.rc.memory.get() == []

    restored = Team.deserialize(tmp_path, context=team.env.context)
    restored_role = restored.env.get_role(role.profile)
    assert type(restored_role) is role_class
    assert restored_role.rc.memory.get() == []
    assert restored_role.is_idle == (message_count == 0)
    assert await restored_role._observe() == message_count
    assert restored_role.rc.memory.get() == messages
    assert restored_role.rc.msg_buffer.empty()
    assert await restored_role._observe() == 0


def test_recover_checkpoint_without_message_buffers(tmp_path):
    role = Role(name="receiver", profile="receiver")
    team = Team(use_mgx=False, roles=[role])
    team.serialize(tmp_path)
    checkpoint_path = tmp_path / "team.json"
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    checkpoint["env"]["roles"][role.profile]["rc"].pop("msg_buffer", None)
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")

    restored = Team.deserialize(tmp_path, context=team.env.context)
    assert restored.env.get_role(role.profile).rc.msg_buffer.empty()


def test_recover_concrete_message_types(tmp_path):
    role = Role(name="receiver", profile="receiver")
    team = Team(use_mgx=False, roles=[role])
    messages = [UserMessage(content="hello"), WwMessage(content="private", restricted_to={"Wolf"})]
    for message in messages:
        role.put_message(message)

    team.serialize(tmp_path)
    restored = Team.deserialize(tmp_path, context=team.env.context)
    pending = restored.env.get_role(role.profile).rc.msg_buffer.pop_all()

    assert [type(message) for message in pending] == [UserMessage, WwMessage]
    assert pending == messages
    assert pending[1].restricted_to == {"Wolf"}


@pytest.mark.asyncio
async def test_pending_messages_survive_failure_checkpoint(tmp_path, mocker):
    role = Role(name="receiver", profile="receiver")
    team = Team(use_mgx=False, roles=[role])
    message = Message(content="pending work", send_to=role.name)
    role.put_message(message)
    mocker.patch("metagpt.team.SERDESER_PATH", tmp_path)
    mocker.patch.object(type(team.env), "run", side_effect=RuntimeError("execution failed"))

    await team.run(n_round=1)

    restored = Team.deserialize(tmp_path / "team", context=team.env.context)
    restored_role = restored.env.get_role(role.profile)
    assert restored_role.rc.memory.get() == []
    assert restored_role.rc.msg_buffer.pop_all() == [message]
    assert role.rc.msg_buffer.pop_all() == [message]


@pytest.mark.asyncio
@pytest.mark.parametrize("message_class", [UserMessage, AIMessage, WwMessage])
async def test_recorded_message_is_not_replayed(tmp_path, message_class):
    role = Role(name="receiver", profile="receiver")
    team = Team(use_mgx=False, roles=[role])
    message = message_class(content="already handled", send_to=role.name)
    role.rc.memory.add(message)
    role.publish_message(message)
    team.serialize(tmp_path)

    restored = Team.deserialize(tmp_path, context=team.env.context).env.get_role(role.profile)
    assert await restored._observe() == 0
    assert restored.rc.memory.get() == [message]
    assert restored.rc.memory.get_by_action(message.cause_by) == [message]
    restored.rc.memory.delete(restored.rc.memory.get()[0])
    assert restored.rc.memory.get() == []
    assert restored.rc.memory.get_by_action(message.cause_by) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("recorded", [False, True])
async def test_recovery_marker_preserves_message_type(tmp_path, recorded):
    role = Role(name="receiver", profile="receiver")
    team = Team(use_mgx=False, roles=[role])
    message = UserMessage(content="interrupted", send_to=role.name)
    role.latest_observed_msg = message
    if recorded:
        role.rc.memory.add(message)
    team.serialize(tmp_path)

    restored = Team.deserialize(tmp_path, context=team.env.context).env.get_role(role.profile)
    assert type(restored.latest_observed_msg) is UserMessage
    assert await restored._observe() == (0 if recorded else 1)
    assert restored.rc.memory.get() == [message]
    assert await restored._observe() == 0


def test_memory_checkpoint_preserves_subtype_equality():
    memory = Memory(ignore_id=True)
    first = WwMessage(content="same", restricted_to={"Wolf"})
    second = WwMessage(content="same", restricted_to={"Seer"})
    memory.add_batch([first, second])

    restored = Memory.model_validate_json(memory.model_dump_json())
    assert restored.get() == [first, second]
    restored.add(first)
    assert restored.count() == 2
    assert "__module_class_name" not in first.model_dump()

    legacy_message = Message(content="legacy")
    legacy = Memory.model_validate({"storage": [legacy_message.model_dump()]})
    assert legacy.get() == [legacy_message]
