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

from metagpt.config import CONFIG
from metagpt.const import DEFAULT_LANGUAGE, DEFAULT_MAX_TOKENS
from metagpt.llm import LLMType
from metagpt.logs import logger
from metagpt.schema import Message, RawMessage
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
    cacheable: bool = True

    def add_talk(self, msg: Message):
        msg.role = "user"
        self.add_history(msg)
        self.is_dirty = True

    def add_answer(self, msg: Message):
        msg.role = "assistant"
        self.add_history(msg)
        self.is_dirty = True

    def get_knowledge(self) -> str:
        texts = [Message(**m).content for m in self.knowledge]
        return "\n".join(texts)

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

    async def summarize(self, llm, max_words=200, keep_language: bool = False, limit: int = -1, **kwargs):
        if self.llm_type == LLMType.METAGPT.value:
            return await self._metagpt_summarize(llm=llm, max_words=max_words, keep_language=keep_language, **kwargs)

        return await self._openai_summarize(
            llm=llm, max_words=max_words, keep_language=keep_language, limit=limit, **kwargs
        )

    async def _openai_summarize(self, llm, max_words=200, keep_language: bool = False, limit: int = -1, **kwargs):
        max_token_count = DEFAULT_MAX_TOKENS
        max_count = 100
        texts = [self.historical_summary]
        for i in self.history:
            m = Message(**i)
            texts.append(m.content)
        text = "\n".join(texts)
        text_length = len(text)
        if limit > 0 and text_length < limit:
            return text
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
                response = await self._get_summary(
                    text=ws, llm=llm, max_words=part_max_words, keep_language=keep_language
                )
                summaries.append(response)
            if len(summaries) == 1:
                summary = summaries[0]
                break

            # Merged and retry
            text = "\n".join(summaries)
            text_length = len(text)

            max_count -= 1  # safeguard
        if summary:
            await self.set_history_summary(history_summary=summary, redis_key=CONFIG.REDIS_KEY, redis_conf=CONFIG.REDIS)
            return summary
        raise openai.InvalidRequestError(message="text too long", param=None)

    async def _metagpt_summarize(self, max_words=200, **kwargs):
        if not self.history:
            return ""

        total_length = 0
        msgs = []
        for i in reversed(self.history):
            m = Message(**i)
            delta = len(m.content)
            if total_length + delta > max_words:
                left = max_words - total_length
                if left == 0:
                    break
                m.content = m.content[0:left]
                msgs.append(m.dict())
                break
            msgs.append(i)
            total_length += delta
        msgs.reverse()
        self.history = msgs
        self.is_dirty = True
        await self.dumps(redis_key=CONFIG.REDIS_KEY, redis_conf=CONFIG.REDIS_CONF)
        self.is_dirty = False

        return BrainMemory.to_metagpt_history_format(self.history)

    @staticmethod
    def to_metagpt_history_format(history) -> str:
        mmsg = []
        for m in history:
            msg = Message(**m)
            r = RawMessage(role="user" if MessageType.Talk.value in msg.tags else "assistant", content=msg.content)
            mmsg.append(r)
        return json.dumps(mmsg)

    @staticmethod
    async def _get_summary(text: str, llm, max_words=20, keep_language: bool = False):
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

    async def get_title(self, llm, max_words=5, **kwargs) -> str:
        """Generate text title"""
        if self.llm_type == LLMType.METAGPT.value:
            return Message(**self.history[0]).content if self.history else "New"

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
        if self.llm_type == LLMType.METAGPT.value:
            return await self._metagpt_is_related(text1=text1, text2=text2, llm=llm)
        return await self._openai_is_related(text1=text1, text2=text2, llm=llm)

    @staticmethod
    async def _metagpt_is_related(**kwargs):
        return False

    @staticmethod
    async def _openai_is_related(text1, text2, llm, **kwargs):
        # command = f"{text1}\n{text2}\n\nIf the two sentences above are related, return [TRUE] brief and clear. Otherwise, return [FALSE]."
        command = f"{text2}\n\nIs there any sentence above related to the following sentence: {text1}.\nIf is there any relevance, return [TRUE] brief and clear. Otherwise, return [FALSE] brief and clear."
        rsp = await llm.aask(msg=command, system_msgs=[])
        result = True if "TRUE" in rsp else False
        p2 = text2.replace("\n", "")
        p1 = text1.replace("\n", "")
        logger.info(f"IS_RELATED:\nParagraph 1: {p2}\nParagraph 2: {p1}\nRESULT: {result}\n")
        return result

    async def rewrite(self, sentence: str, context: str, llm):
        if self.llm_type == LLMType.METAGPT.value:
            return await self._metagpt_rewrite(sentence=sentence, context=context, llm=llm)
        return await self._openai_rewrite(sentence=sentence, context=context, llm=llm)

    async def _metagpt_rewrite(self, sentence: str, **kwargs):
        return sentence

    async def _openai_rewrite(self, sentence: str, context: str, llm, **kwargs):
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

    def set_llm_type(self, v):
        if v and v != self.llm_type:
            self.llm_type = v
            self.is_dirty = True

    @property
    def is_history_available(self):
        return bool(self.history or self.historical_summary)

    @property
    def history_text(self):
        if self.llm_type == LLMType.METAGPT.value:
            return self._get_metagpt_history_text()
        return self._get_openai_history_text()

    def _get_metagpt_history_text(self):
        return BrainMemory.to_metagpt_history_format(self.history)

    def _get_openai_history_text(self):
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

    DEFAULT_TOKEN_SIZE = 500
