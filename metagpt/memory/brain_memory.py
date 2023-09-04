#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : brain_memory.py
@Desc    : Support memory for multiple tasks and multiple mainlines.
"""
import hashlib
import json
from enum import Enum
from typing import Dict, List

import pydantic

from metagpt import Message
from metagpt.utils.redis import Redis


class MessageType(Enum):
    Talk = "TALK"
    Solution = "SOLUTION"
    Problem = "PROBLEM"
    Skill = "SKILL"
    Answer = "ANSWER"


class BrainMemory(pydantic.BaseModel):
    history: List[Dict] = []
    stack: List[Dict] = []
    solution: List[Dict] = []
    knowledge: List[Dict] = []
    # If the fingerprint of the history text is found in the `historical_summary_fingerprint`,
    # it indicates that the text has already been incorporated into the `history summary`.
    historical_summary_fingerprint: List[str] = []
    historical_summary: str = ""
    last_history_id: str = ""

    def add_talk(self, msg: Message):
        msg.add_tag(MessageType.Talk.value)
        self.history.append(msg.dict())

    def add_answer(self, msg: Message):
        msg.add_tag(MessageType.Answer.value)
        self.history.append(msg.dict())

    def get_knowledge(self) -> str:
        texts = [Message(**m).content for m in self.knowledge]
        return "\n".join(texts)

    @property
    def history_text(self):
        if len(self.history) == 0:
            return ""
        texts = []
        for m in self.history[:-1]:
            if isinstance(m, Dict):
                t = Message(**m).content
            elif isinstance(m, Message):
                t = m.content
            else:
                continue
            texts.append(t)

        return "\n".join(texts)

    def move_to_solution(self, history_summary):
        """Put it in the solution queue for future long-term retrieval.
        This functionality hasn't been added yet, so use the history summary as a temporary substitute for now."""
        pass
        # if len(self.history) < 2:
        #     return
        # msgs = self.history[:-1]
        # self.solution.extend(msgs)
        # if not Message(**self.history[-1]).is_contain(MessageType.Talk.value):
        #     self.solution.append(self.history[-1])
        #     self.history = []
        # else:
        #     self.history = self.history[-1:]
        # self.history.insert(0, Message(content="RESOLVED: " + history_summary))

    @property
    def last_talk(self):
        if len(self.history) == 0:
            return None
        last_msg = Message(**self.history[-1])
        if not last_msg.is_contain(MessageType.Talk.value):
            return None
        return last_msg.content

    @staticmethod
    def get_md5(text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    @staticmethod
    async def loads(redis_key: str) -> "BrainMemory":
        redis = Redis()
        if not redis.is_valid() or not redis_key:
            return BrainMemory()
        v = await redis.get(key=redis_key)
        if not v:
            data = json.loads(v)
            return BrainMemory(**data)
        return BrainMemory()

    async def dumps(self, redis_key: str, timeout_sec: int = 30 * 60):
        redis = Redis()
        if not redis.is_valid() or not redis_key:
            return False
        v = self.json()
        await redis.set(key=redis_key, data=v, timeout_sec=timeout_sec)
