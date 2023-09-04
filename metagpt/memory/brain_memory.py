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
from metagpt.logs import logger
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
    historical_summary: str = ""
    last_history_id: str = ""
    is_dirty: bool = False

    def add_talk(self, msg: Message):
        msg.add_tag(MessageType.Talk.value)
        self.history.append(msg.dict())
        self.is_dirty = True

    def add_answer(self, msg: Message):
        msg.add_tag(MessageType.Answer.value)
        self.history.append(msg.dict())
        self.is_dirty = True

    def get_knowledge(self) -> str:
        texts = [Message(**m).content for m in self.knowledge]
        return "\n".join(texts)

    @property
    def history_text(self):
        if len(self.history) == 0 and not self.historical_summary:
            return ""
        texts = [self.historical_summary] if self.historical_summary else []
        for m in self.history[:-1]:
            if isinstance(m, Dict):
                t = Message(**m).content
            elif isinstance(m, Message):
                t = m.content
            else:
                continue
            texts.append(t)

        return "\n".join(texts)

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
    async def loads(redis_key: str, redis_conf: Dict = None) -> "BrainMemory":
        redis = Redis(conf=redis_conf)
        if not redis.is_valid() or not redis_key:
            return BrainMemory()
        v = await redis.get(key=redis_key)
        logger.info(f"REDIS GET {redis_key} {v}")
        if v:
            data = json.loads(v)
            bm = BrainMemory(**data)
            bm.is_dirty = False
            return bm
        return BrainMemory()

    async def dumps(self, redis_key: str, timeout_sec: int = 30 * 60, redis_conf: Dict = None):
        redis = Redis(conf=redis_conf)
        if not redis.is_valid() or not redis_key:
            return False
        v = self.json()
        await redis.set(key=redis_key, data=v, timeout_sec=timeout_sec)
        logger.info(f"REDIS SET {redis_key} {v}")
        self.is_dirty = False

    @staticmethod
    def to_redis_key(prefix: str, user_id: str, chat_id: str):
        return f"{prefix}:{chat_id}:{user_id}"

    async def set_history_summary(self, history_summary, redis_key, redis_conf):
        if self.historical_summary == history_summary:
            if self.is_dirty:
                await self.dumps(redis_key=redis_key, redis_conf=redis_conf)
                self.is_dirty = False
            return

        self.historical_summary = history_summary
        self.history = []
        await self.dumps(redis_key=redis_key, redis_conf=redis_conf)
        self.is_dirty = False

    def add_history(self, msg: Message):
        if msg.id:
            if int(msg.id) < int(self.last_history_id):
                return
        self.history.append(msg.dict())
        self.is_dirty = True

    def exists(self, text) -> bool:
        for m in reversed(self.history):
            if m.get("content") == text:
                return True
        return False
