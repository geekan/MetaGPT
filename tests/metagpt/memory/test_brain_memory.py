#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/27
@Author  : mashenquan
@File    : test_brain_memory.py
"""

import pytest

from metagpt.llm import LLM
from metagpt.memory.brain_memory import BrainMemory
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_memory():
    memory = BrainMemory()
    memory.add_talk(Message(content="talk"))
    assert memory.history[0].role == "user"
    memory.add_answer(Message(content="answer"))
    assert memory.history[1].role == "assistant"
    redis_key = BrainMemory.to_redis_key("none", "user_id", "chat_id")
    await memory.dumps(redis_key=redis_key)
    assert memory.exists("talk")
    assert 1 == memory.to_int("1", 0)
    memory.last_talk = "AAA"
    assert memory.pop_last_talk() == "AAA"
    assert memory.last_talk is None
    assert memory.is_history_available
    assert memory.history_text

    memory = await BrainMemory.loads(redis_key=redis_key)
    assert memory


@pytest.mark.parametrize(
    ("input", "tag", "val"),
    [("[TALK]:Hello", "TALK", "Hello"), ("Hello", None, "Hello"), ("[TALK]Hello", None, "[TALK]Hello")],
)
def test_extract_info(input, tag, val):
    t, v = BrainMemory.extract_info(input)
    assert tag == t
    assert val == v


@pytest.mark.asyncio
@pytest.mark.parametrize("llm", [LLM()])
async def test_memory_llm(llm):
    memory = BrainMemory()
    for i in range(500):
        memory.add_talk(Message(content="Lily is a girl.\n"))

    res = await memory.is_related("apple", "moon", llm)
    assert not res

    res = await memory.rewrite(sentence="apple Lily eating", context="", llm=llm)
    assert "Lily" in res

    res = await memory.summarize(llm=llm)
    assert res

    res = await memory.get_title(llm=llm)
    assert res
    assert "Lily" in res
    assert memory.history or memory.historical_summary


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
