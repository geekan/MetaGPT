#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : brain_memory.py
@Desc    : Used by AgentStore. Used for long-term storage and automatic compression.
@Modified By: mashenquan, 2023/9/4. + redis memory cache.
@Modified By: mashenquan, 2023/12/25. Simplify Functionality.
"""
import json
import re
from typing import Dict, List

from pydantic import BaseModel, Field

from metagpt.config import CONFIG
from metagpt.const import DEFAULT_LANGUAGE
from metagpt.logs import logger
from metagpt.provider import MetaGPTAPI
from metagpt.schema import Message, SimpleMessage
from metagpt.utils.redis import Redis


class BrainMemory(BaseModel):
    history: List[Message] = Field(default_factory=list)
    knowledge: List[Message] = Field(default_factory=list)
    historical_summary: str = ""
    last_history_id: str = ""
    is_dirty: bool = False
    last_talk: str = None
    cacheable: bool = True

    def add_talk(self, msg: Message):
        """
        Add message from user.
        """
        msg.role = "user"
        self.add_history(msg)
        self.is_dirty = True

    def add_answer(self, msg: Message):
        """Add message from LLM"""
        msg.role = "assistant"
        self.add_history(msg)
        self.is_dirty = True

    def get_knowledge(self) -> str:
        texts = [m.content for m in self.knowledge]
        return "\n".join(texts)

    @staticmethod
    async def loads(redis_key: str, redis_conf: Dict = None) -> "BrainMemory":
        redis = Redis(conf=redis_conf)
        if not redis.is_valid() or not redis_key:
            return BrainMemory()
        v = await redis.get(key=redis_key)
        logger.debug(f"REDIS GET {redis_key} {v}")
        if v:
            bm = BrainMemory.parse_raw(v)
            bm.is_dirty = False
            return bm
        return BrainMemory()

    async def dumps(self, redis_key: str, timeout_sec: int = 30 * 60, redis_conf: Dict = None):
        if not self.is_dirty:
            return
        redis = Redis(conf=redis_conf)
        if not redis.is_valid() or not redis_key:
            return False
        v = self.model_dump_json()
        if self.cacheable:
            await redis.set(key=redis_key, data=v, timeout_sec=timeout_sec)
            logger.debug(f"REDIS SET {redis_key} {v}")
        self.is_dirty = False

    @staticmethod
    def to_redis_key(prefix: str, user_id: str, chat_id: str):
        return f"{prefix}:{user_id}:{chat_id}"

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
        self.history.append(msg.model_dump())
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

    async def summarize(self, llm, max_words=200, keep_language: bool = False, limit: int = -1, **kwargs):
        if isinstance(llm, MetaGPTAPI):
            return await self._metagpt_summarize(max_words=max_words)

        return await self._openai_summarize(llm=llm, max_words=max_words, keep_language=keep_language, limit=limit)

    async def _openai_summarize(self, llm, max_words=200, keep_language: bool = False, limit: int = -1):
        texts = [self.historical_summary]
        for m in self.history:
            texts.append(m.content)
        text = "\n".join(texts)

        text_length = len(text)
        if limit > 0 and text_length < limit:
            return text
        summary = await llm.summarize(text=text, max_words=max_words, keep_language=keep_language, limit=limit)
        if summary:
            await self.set_history_summary(history_summary=summary, redis_key=CONFIG.REDIS_KEY, redis_conf=CONFIG.REDIS)
            return summary
        raise ValueError(f"text too long:{text_length}")

    async def _metagpt_summarize(self, max_words=200):
        if not self.history:
            return ""

        total_length = 0
        msgs = []
        for m in reversed(self.history):
            delta = len(m.content)
            if total_length + delta > max_words:
                left = max_words - total_length
                if left == 0:
                    break
                m.content = m.content[0:left]
                msgs.append(m.model_dump())
                break
            msgs.append(m)
            total_length += delta
        msgs.reverse()
        self.history = msgs
        self.is_dirty = True
        await self.dumps(redis_key=CONFIG.REDIS_KEY, redis_conf=CONFIG.REDIS_CONF)
        self.is_dirty = False

        return BrainMemory.to_metagpt_history_format(self.history)

    @staticmethod
    def to_metagpt_history_format(history) -> str:
        mmsg = [SimpleMessage(role=m.role, content=m.content) for m in history]
        return json.dumps(mmsg)

    async def get_title(self, llm, max_words=5, **kwargs) -> str:
        """Generate text title"""
        if isinstance(llm, MetaGPTAPI):
            return self.history[0].content if self.history else "New"

        summary = await self.summarize(llm=llm, max_words=500)

        language = CONFIG.language or DEFAULT_LANGUAGE
        command = f"Translate the above summary into a {language} title of less than {max_words} words."
        summaries = [summary, command]
        msg = "\n".join(summaries)
        logger.debug(f"title ask:{msg}")
        response = await llm.aask(msg=msg, system_msgs=[])
        logger.debug(f"title rsp: {response}")
        return response

    async def is_related(self, text1, text2, llm):
        if isinstance(llm, MetaGPTAPI):
            return await self._metagpt_is_related(text1=text1, text2=text2, llm=llm)
        return await self._openai_is_related(text1=text1, text2=text2, llm=llm)

    @staticmethod
    async def _metagpt_is_related(**kwargs):
        return False

    @staticmethod
    async def _openai_is_related(text1, text2, llm, **kwargs):
        command = (
            f"{text2}\n\nIs there any sentence above related to the following sentence: {text1}.\nIf is there "
            "any relevance, return [TRUE] brief and clear. Otherwise, return [FALSE] brief and clear."
        )
        rsp = await llm.aask(msg=command, system_msgs=[])
        result = True if "TRUE" in rsp else False
        p2 = text2.replace("\n", "")
        p1 = text1.replace("\n", "")
        logger.info(f"IS_RELATED:\nParagraph 1: {p2}\nParagraph 2: {p1}\nRESULT: {result}\n")
        return result

    async def rewrite(self, sentence: str, context: str, llm):
        if isinstance(llm, MetaGPTAPI):
            return await self._metagpt_rewrite(sentence=sentence, context=context, llm=llm)
        return await self._openai_rewrite(sentence=sentence, context=context, llm=llm)

    @staticmethod
    async def _metagpt_rewrite(sentence: str):
        return sentence

    @staticmethod
    async def _openai_rewrite(sentence: str, context: str, llm):
        command = (
            f"{context}\n\nExtract relevant information from every preceding sentence and use it to succinctly "
            f"supplement or rewrite the following text in brief and clear:\n{sentence}"
        )
        rsp = await llm.aask(msg=command, system_msgs=[])
        logger.info(f"REWRITE:\nCommand: {command}\nRESULT: {rsp}\n")
        return rsp

    @staticmethod
    def extract_info(input_string, pattern=r"\[([A-Z]+)\]:\s*(.+)"):
        match = re.match(pattern, input_string)
        if match:
            return match.group(1), match.group(2)
        else:
            return None, input_string

    @property
    def is_history_available(self):
        return bool(self.history or self.historical_summary)

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
