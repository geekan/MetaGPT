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
import re
from enum import Enum
from typing import Dict, List, Optional

import openai
import pydantic

from metagpt import Message
from metagpt.config import CONFIG
from metagpt.const import DEFAULT_LANGUAGE, DEFAULT_MAX_TOKENS
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
    llm_type: Optional[str] = None

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

    # @property
    # def history_text(self):
    #     if len(self.history) == 0 and not self.historical_summary:
    #         return ""
    #     try:
    #         self.loads_raw_messages()
    #         return self.dumps_raw_messages()
    #     except:
    #         texts = [self.historical_summary] if self.historical_summary else []
    #         for m in self.history[:-1]:
    #             if isinstance(m, Dict):
    #                 t = Message(**m).content
    #             elif isinstance(m, Message):
    #                 t = m.content
    #             else:
    #                 continue
    #             texts.append(t)
    #
    #         return "\n".join(texts)

    @staticmethod
    async def loads(redis_key: str, redis_conf: Dict = None) -> "BrainMemory":
        redis = Redis(conf=redis_conf)
        if not redis.is_valid() or not redis_key:
            return BrainMemory(llm_type=CONFIG.LLM_TYPE)
        v = await redis.get(key=redis_key)
        logger.debug(f"REDIS GET {redis_key} {v}")
        if v:
            data = json.loads(v)
            bm = BrainMemory(**data)
            bm.is_dirty = False
            return bm
        return BrainMemory(llm_type=CONFIG.LLM_TYPE)

    async def dumps(self, redis_key: str, timeout_sec: int = 30 * 60, redis_conf: Dict = None):
        if not self.is_dirty:
            return
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

    async def summerize(self, llm, max_words=200, keep_language: bool = False, **kwargs):
        max_token_count = DEFAULT_MAX_TOKENS
        max_count = 100
        text = self.history_text
        text_length = len(text)
        summary = ""
        while max_count > 0:
            if text_length < max_token_count:
                summary = await self._get_summary(text=text, llm=llm, max_words=max_words, keep_language=keep_language)
                break

            padding_size = 20 if max_token_count > 20 else 0
            text_windows = self.split_texts(text, window_size=max_token_count - padding_size)
            part_max_words = min(int(max_words / len(text_windows)) + 1, 100)
            summaries = []
            for ws in text_windows:
                response = await self._get_summary(text=ws, max_words=part_max_words, keep_language=keep_language)
                summaries.append(response)
            if len(summaries) == 1:
                summary = summaries[0]
                break

            # Merged and retry
            text = "\n".join(summaries)
            text_length = len(text)

            max_count -= 1  # safeguard
        if not summary:
            await self.set_history_summary(history_summary=summary, redis_key=CONFIG.REDIS_KEY, redis_conf=CONFIG.REDIS)
            return summary

        raise openai.error.InvalidRequestError("text too long")

    async def _get_summary(self, text: str, llm, max_words=20, keep_language: bool = False):
        """Generate text summary"""
        if len(text) < max_words:
            return text
        if keep_language:
            command = f".Translate the above content into a summary of less than {max_words} words in language of the content strictly."
        else:
            command = f"Translate the above content into a summary of less than {max_words} words."
        msg = text + "\n\n" + command
        logger.debug(f"summary ask:{msg}")
        response = await llm.aask(msg=msg, system_msgs=[])
        logger.debug(f"summary rsp: {response}")
        return response

    async def get_title(self, text: str, llm, max_words=5, **kwargs) -> str:
        """Generate text title"""
        summary = await self.get_summary(text, max_words=500)

        language = CONFIG.language or DEFAULT_LANGUAGE
        command = f"Translate the above summary into a {language} title of less than {max_words} words."
        summaries = [summary, command]
        msg = "\n".join(summaries)
        logger.debug(f"title ask:{msg}")
        response = await llm.aask(msg=msg, system_msgs=[])
        logger.debug(f"title rsp: {response}")
        return response

    async def is_related(self, text1, text2, llm):
        # command = f"{text1}\n{text2}\n\nIf the two sentences above are related, return [TRUE] brief and clear. Otherwise, return [FALSE]."
        command = f"{text2}\n\nIs there any sentence above related to the following sentence: {text1}.\nIf is there any relevance, return [TRUE] brief and clear. Otherwise, return [FALSE] brief and clear."
        rsp = await llm.aask(msg=command, system_msgs=[])
        result = True if "TRUE" in rsp else False
        p2 = text2.replace("\n", "")
        p1 = text1.replace("\n", "")
        logger.info(f"IS_RELATED:\nParagraph 1: {p2}\nParagraph 2: {p1}\nRESULT: {result}\n")
        return result

    async def rewrite(self, sentence: str, context: str, llm):
        # command = (
        #     f"{context}\n\nConsidering the content above, rewrite and return this sentence brief and clear:\n{sentence}"
        # )
        command = f"{context}\n\nExtract relevant information from every preceding sentence and use it to succinctly supplement or rewrite the following text in brief and clear:\n{sentence}"
        rsp = await llm.aask(msg=command, system_msgs=[])
        logger.info(f"REWRITE:\nCommand: {command}\nRESULT: {rsp}\n")
        return rsp

    @staticmethod
    def split_texts(text: str, window_size) -> List[str]:
        """Splitting long text into sliding windows text"""
        if window_size <= 0:
            window_size = BrainMemory.DEFAULT_TOKEN_SIZE
        total_len = len(text)
        if total_len <= window_size:
            return [text]

        padding_size = 20 if window_size > 20 else 0
        windows = []
        idx = 0
        data_len = window_size - padding_size
        while idx < total_len:
            if window_size + idx > total_len:  # 不足一个滑窗
                windows.append(text[idx:])
                break
            # 每个窗口少算padding_size自然就可实现滑窗功能, 比如: [1, 2, 3, 4, 5, 6, 7, ....]
            # window_size=3, padding_size=1：
            # [1, 2, 3], [3, 4, 5], [5, 6, 7], ....
            #   idx=2,  |  idx=5   |  idx=8  | ...
            w = text[idx : idx + window_size]
            windows.append(w)
            idx += data_len

        return windows

    @staticmethod
    def extract_info(input_string, pattern=r"\[([A-Z]+)\]:\s*(.+)"):
        match = re.match(pattern, input_string)
        if match:
            return match.group(1), match.group(2)
        else:
            return None, input_string

    DEFAULT_TOKEN_SIZE = 500
