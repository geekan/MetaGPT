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
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from metagpt.config2 import config
from metagpt.const import DEFAULT_MAX_TOKENS, DEFAULT_TOKEN_SIZE
from metagpt.logs import logger
from metagpt.provider import MetaGPTLLM
from metagpt.provider.base_llm import BaseLLM
from metagpt.schema import Message, SimpleMessage
from metagpt.utils.redis import Redis


class BrainMemory(BaseModel):
    history: List[Message] = Field(default_factory=list)
    knowledge: List[Message] = Field(default_factory=list)
    historical_summary: str = ""
    last_history_id: str = ""
    is_dirty: bool = False
    last_talk: Optional[str] = None
    cacheable: bool = True
    llm: Optional[BaseLLM] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True

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
    async def loads(redis_key: str) -> "BrainMemory":
        redis = Redis(config.redis)
        if not redis_key:
            return BrainMemory()
        v = await redis.get(key=redis_key)
        logger.debug(f"REDIS GET {redis_key} {v}")
        if v:
            bm = BrainMemory.parse_raw(v)
            bm.is_dirty = False
            return bm
        return BrainMemory()

    async def dumps(self, redis_key: str, timeout_sec: int = 30 * 60):
        if not self.is_dirty:
            return
        redis = Redis(config.redis)
        if not redis_key:
            return False
        v = self.model_dump_json()
        if self.cacheable:
            await redis.set(key=redis_key, data=v, timeout_sec=timeout_sec)
            logger.debug(f"REDIS SET {redis_key} {v}")
        self.is_dirty = False

    @staticmethod
    def to_redis_key(prefix: str, user_id: str, chat_id: str):
        return f"{prefix}:{user_id}:{chat_id}"

    async def set_history_summary(self, history_summary, redis_key):
        if self.historical_summary == history_summary:
            if self.is_dirty:
                await self.dumps(redis_key=redis_key)
                self.is_dirty = False
            return

        self.historical_summary = history_summary
        self.history = []
        await self.dumps(redis_key=redis_key)
        self.is_dirty = False

    def add_history(self, msg: Message):
        if msg.id:
            if self.to_int(msg.id, 0) <= self.to_int(self.last_history_id, -1):
                return

        self.history.append(msg)
        self.last_history_id = str(msg.id)
        self.is_dirty = True

    def exists(self, text) -> bool:
        for m in reversed(self.history):
            if m.content == text:
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
        if isinstance(llm, MetaGPTLLM):
            return await self._metagpt_summarize(max_words=max_words)

        self.llm = llm
        return await self._openai_summarize(llm=llm, max_words=max_words, keep_language=keep_language, limit=limit)

    async def _openai_summarize(self, llm, max_words=200, keep_language: bool = False, limit: int = -1):
        texts = [self.historical_summary]
        for m in self.history:
            texts.append(m.content)
        text = "\n".join(texts)

        text_length = len(text)
        if limit > 0 and text_length < limit:
            return text
        summary = await self._summarize(text=text, max_words=max_words, keep_language=keep_language, limit=limit)
        if summary:
            await self.set_history_summary(history_summary=summary, redis_key=config.redis_key)
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
                msgs.append(m)
                break
            msgs.append(m)
            total_length += delta
        msgs.reverse()
        self.history = msgs
        self.is_dirty = True
        await self.dumps(redis_key=config.redis.key)
        self.is_dirty = False

        return BrainMemory.to_metagpt_history_format(self.history)

    @staticmethod
    def to_metagpt_history_format(history) -> str:
        mmsg = [SimpleMessage(role=m.role, content=m.content).model_dump() for m in history]
        return json.dumps(mmsg, ensure_ascii=False)

    async def get_title(self, llm, max_words=5, **kwargs) -> str:
        """Generate text title"""
        if isinstance(llm, MetaGPTLLM):
            return self.history[0].content if self.history else "New"

        summary = await self.summarize(llm=llm, max_words=500)

        language = config.language
        command = f"Translate the above summary into a {language} title of less than {max_words} words."
        summaries = [summary, command]
        msg = "\n".join(summaries)
        logger.debug(f"title ask:{msg}")
        response = await llm.aask(msg=msg, system_msgs=[], stream=False)
        logger.debug(f"title rsp: {response}")
        return response

    async def is_related(self, text1, text2, llm):
        if isinstance(llm, MetaGPTLLM):
            return await self._metagpt_is_related(text1=text1, text2=text2, llm=llm)
        return await self._openai_is_related(text1=text1, text2=text2, llm=llm)

    @staticmethod
    async def _metagpt_is_related(**kwargs):
        return False

    @staticmethod
    async def _openai_is_related(text1, text2, llm, **kwargs):
        context = f"## Paragraph 1\n{text2}\n---\n## Paragraph 2\n{text1}\n"
        rsp = await llm.aask(
            msg=context,
            system_msgs=[
                "You are a tool capable of determining whether two paragraphs are semantically related."
                'Return "TRUE" if "Paragraph 1" is semantically relevant to "Paragraph 2", otherwise return "FALSE".'
            ],
            stream=False,
        )
        result = True if "TRUE" in rsp else False
        p2 = text2.replace("\n", "")
        p1 = text1.replace("\n", "")
        logger.info(f"IS_RELATED:\nParagraph 1: {p2}\nParagraph 2: {p1}\nRESULT: {result}\n")
        return result

    async def rewrite(self, sentence: str, context: str, llm):
        if isinstance(llm, MetaGPTLLM):
            return await self._metagpt_rewrite(sentence=sentence, context=context, llm=llm)
        return await self._openai_rewrite(sentence=sentence, context=context, llm=llm)

    @staticmethod
    async def _metagpt_rewrite(sentence: str, **kwargs):
        return sentence

    @staticmethod
    async def _openai_rewrite(sentence: str, context: str, llm):
        prompt = f"## Context\n{context}\n---\n## Sentence\n{sentence}\n"
        rsp = await llm.aask(
            msg=prompt,
            system_msgs=[
                'You are a tool augmenting the "Sentence" with information from the "Context".',
                "Do not supplement the context with information that is not present, especially regarding the subject and object.",
                "Return the augmented sentence.",
            ],
            stream=False,
        )
        logger.info(f"REWRITE:\nCommand: {prompt}\nRESULT: {rsp}\n")
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

    async def _summarize(self, text: str, max_words=200, keep_language: bool = False, limit: int = -1) -> str:
        max_token_count = DEFAULT_MAX_TOKENS
        max_count = 100
        text_length = len(text)
        if limit > 0 and text_length < limit:
            return text
        summary = ""
        while max_count > 0:
            if text_length < max_token_count:
                summary = await self._get_summary(text=text, max_words=max_words, keep_language=keep_language)
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
        return summary

    async def _get_summary(self, text: str, max_words=20, keep_language: bool = False):
        """Generate text summary"""
        if len(text) < max_words:
            return text
        system_msgs = [
            "You are a tool for summarizing and abstracting text.",
            f"Return the summarized text to less than {max_words} words.",
        ]
        if keep_language:
            system_msgs.append("The generated summary should be in the same language as the original text.")
        response = await self.llm.aask(msg=text, system_msgs=system_msgs, stream=False)
        logger.debug(f"{text}\nsummary rsp: {response}")
        return response

    @staticmethod
    def split_texts(text: str, window_size) -> List[str]:
        """Splitting long text into sliding windows text"""
        if window_size <= 0:
            window_size = DEFAULT_TOKEN_SIZE
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
