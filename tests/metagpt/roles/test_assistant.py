#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/25
@Author  : mashenquan
@File    : test_asssistant.py
@Desc    : Used by AgentStore.
"""

import pytest
from pydantic import BaseModel

from metagpt.actions.skill_action import SkillAction
from metagpt.actions.talk_action import TalkAction
from metagpt.memory.brain_memory import BrainMemory
from metagpt.roles.assistant import Assistant
from metagpt.schema import Message
from metagpt.utils.common import any_to_str


@pytest.mark.asyncio
async def test_run(mocker, context):
    # mock
    mocker.patch("metagpt.learn.text_to_image", return_value="http://mock.com/1.png")

    context.kwargs.language = "Chinese"

    class Input(BaseModel):
        memory: BrainMemory
        language: str
        agent_description: str
        cause_by: str
        agent_skills: list

    agent_skills = [
        {"id": 1, "name": "text_to_speech", "type": "builtin", "config": {}, "enabled": True},
        {"id": 2, "name": "text_to_image", "type": "builtin", "config": {}, "enabled": True},
        {"id": 3, "name": "ai_call", "type": "builtin", "config": {}, "enabled": True},
        {"id": 3, "name": "data_analysis", "type": "builtin", "config": {}, "enabled": True},
        {"id": 5, "name": "crawler", "type": "builtin", "config": {"engine": "ddg"}, "enabled": True},
        {"id": 6, "name": "knowledge", "type": "builtin", "config": {}, "enabled": True},
        {"id": 6, "name": "web_search", "type": "builtin", "config": {}, "enabled": True},
    ]

    inputs = [
        {
            "memory": {
                "history": [
                    {
                        "content": "who is tulin",
                        "role": "user",
                        "id": "1",
                    },
                    {"content": "The one who eaten a poison apple.", "role": "assistant"},
                ],
                "knowledge": [{"content": "tulin is a scientist."}],
                "last_talk": "Do you have a poison apple?",
            },
            "language": "English",
            "agent_description": "chatterbox",
            "cause_by": any_to_str(TalkAction),
            "agent_skills": [],
        },
        {
            "memory": {
                "history": [
                    {
                        "content": "can you draw me an picture?",
                        "role": "user",
                        "id": "1",
                    },
                    {"content": "Yes, of course. What do you want me to draw", "role": "assistant"},
                ],
                "knowledge": [{"content": "tulin is a scientist."}],
                "last_talk": "Draw me an apple.",
            },
            "language": "English",
            "agent_description": "painter",
            "cause_by": any_to_str(SkillAction),
            "agent_skills": agent_skills,
        },
    ]

    for i in inputs:
        seed = Input(**i)
        role = Assistant(language="Chinese", context=context)
        role.context.kwargs.language = seed.language
        role.context.kwargs.agent_description = seed.agent_description
        role.context.kwargs.agent_skills = seed.agent_skills

        role.memory = seed.memory  # Restore historical conversation content.
        while True:
            has_action = await role.think()
            if not has_action:
                break
            msg: Message = await role.act()
            # logger.info(msg)
            assert msg
            assert msg.cause_by == seed.cause_by
            assert msg.content


@pytest.mark.parametrize(
    "memory",
    [
        {
            "history": [
                {
                    "content": "can you draw me an picture?",
                    "role": "user",
                    "id": "1",
                },
                {"content": "Yes, of course. What do you want me to draw", "role": "assistant"},
            ],
            "knowledge": [{"content": "tulin is a scientist."}],
            "last_talk": "Draw me an apple.",
        }
    ],
)
@pytest.mark.asyncio
async def test_memory(memory, context):
    role = Assistant(context=context)
    role.context.kwargs.agent_skills = []
    role.load_memory(memory)

    val = role.get_memory()
    assert val

    await role.talk("draw apple")
    await role.think()
    assert isinstance(role.rc.todo, TalkAction)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
