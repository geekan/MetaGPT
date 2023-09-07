#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : brain_memory.py
@Desc    : Support memory for multiple tasks and multiple mainlines.
@Modified By: mashenquan, 2023/9/4. + redis memory cache.
"""
import json
from enum import Enum
from typing import Dict, List

import pydantic

from metagpt import Message
from metagpt.logs import logger
from metagpt.schema import RawMessage
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
    last_talk: str = None

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
        try:
            self.loads_raw_messages()
            return self.dumps_raw_messages()
        except:
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

    @staticmethod
    async def loads(redis_key: str, redis_conf: Dict = None) -> "BrainMemory":
        redis = Redis(conf=redis_conf)
        if not redis.is_valid() or not redis_key:
            return BrainMemory()
        v = await redis.get(key=redis_key)
        logger.debug(f"REDIS GET {redis_key} {v}")
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
        logger.debug(f"REDIS SET {redis_key} {v}")
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
            if self.to_int(msg.id, 0) <= self.to_int(self.last_history_id, -1):
                return
        self.history.append(msg.dict())
        self.last_history_id = str(msg.id)
        self.is_dirty = True

    def exists(self, text) -> bool:
        for m in reversed(self.history):
            if m.get("content") == text:
                return True
        return False

    @staticmethod
    def to_int(v, default_value):
        try:
            return int(v)
        except:
            return default_value

    def pop_last_talk(self):
        v = self.last_talk
        self.last_talk = None
        return v

    def loads_raw_messages(self):
        if not self.historical_summary:
            return
        vv = json.loads(self.historical_summary)
        msgs = []
        for v in vv:
            tag = set([MessageType.Talk.value]) if v.get("role") == "user" else set([MessageType.Answer.value])
            m = Message(content=v.get("content"), tags=tag)
            msgs.append(m)
        msgs.extend(self.history)
        self.history = msgs
        self.is_dirty = True

    def dumps_raw_messages(self, max_length: int = 0) -> str:
        summary = []

        total_length = 0
        for m in reversed(self.history):
            msg = Message(**m)
            c = RawMessage(role="user" if MessageType.Talk.value in msg.tags else "assistant", content=msg.content)
            length_delta = len(msg.content)
            if max_length > 0:
                if total_length + length_delta > max_length:
                    left = max_length - total_length
                    if left > 0:
                        c.content = msg.content[0:left]
                        summary.insert(0, c)
                    break

            total_length += length_delta
            summary.insert(0, c)

        self.historical_summary = json.dumps(summary)
        self.history = []
        self.is_dirty = True
        return self.historical_summary
