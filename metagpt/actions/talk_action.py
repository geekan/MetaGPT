#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/28
@Author  : mashenquan
@File    : talk_action.py
@Desc    : Act as it’s a talk
"""
import json

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.const import DEFAULT_LANGUAGE
from metagpt.llm import LLMType
from metagpt.logs import logger


class TalkAction(Action):
    def __init__(self, name: str = "", talk="", history_summary="", knowledge="", context=None, llm=None, **kwargs):
        context = context or {}
        context["talk"] = talk
        context["history_summery"] = history_summary
        context["knowledge"] = knowledge
        super(TalkAction, self).__init__(name=name, context=context, llm=llm)
        self._talk = talk
        self._history_summary = history_summary
        self._knowledge = knowledge
        self._rsp = None

    @property
    def prompt(self):
        prompt = ""
        if CONFIG.agent_description:
            prompt = (
                f"You are {CONFIG.agent_description}. Your responses should align with the role-play agreement, "
                f"maintaining the character's persona and habits. When faced with unrelated questions, playfully "
                f"decline to answer without revealing your AI nature to preserve the character's image.\n\n"
            )
        prompt += f"Knowledge:\n{self._knowledge}\n\n" if self._knowledge else ""
        prompt += f"{self._history_summary}\n\n"
        prompt += (
            "If the information is insufficient, you can search in the historical conversation or knowledge above.\n"
        )
        language = CONFIG.language or DEFAULT_LANGUAGE
        prompt += (
            f"Answer the following questions strictly in {language}, and the answers must follow the Markdown format.\n "
            f"{self._talk}"
        )
        logger.debug(f"PROMPT: {prompt}")
        return prompt

    @property
    def prompt_gpt4(self):
        kvs = {
            "{role}": CONFIG.agent_description or "",
            "{history}": self._history_summary or "",
            "{knowledge}": self._knowledge or "",
            "{language}": CONFIG.language or DEFAULT_LANGUAGE,
            "{ask}": self._talk,
        }
        prompt = TalkAction.__FORMATION_LOOSE__
        for k, v in kvs.items():
            prompt = prompt.replace(k, v)
        logger.info(f"PROMPT: {prompt}")
        return prompt

    async def run_old(self, *args, **kwargs) -> ActionOutput:
        prompt = self.prompt
        rsp = await self.llm.aask(msg=prompt, system_msgs=[])
        logger.debug(f"PROMPT:{prompt}\nRESULT:{rsp}\n")
        self._rsp = ActionOutput(content=rsp)
        return self._rsp

    @property
    def aask_args(self):
        language = CONFIG.language or DEFAULT_LANGUAGE
        system_msgs = [
            f"You are {CONFIG.agent_description}.",
            "Your responses should align with the role-play agreement, "
            "maintaining the character's persona and habits. When faced with unrelated questions, playfully "
            "decline to answer without revealing your AI nature to preserve the character's image.",
            "If the information is insufficient, you can search in the context or knowledge.",
            f"Answer the following questions strictly in {language}, and the answers must follow the Markdown format.",
        ]
        format_msgs = []
        if self._knowledge:
            format_msgs.append({"role": "assistant", "content": self._knowledge})
        if self._history_summary:
            if CONFIG.LLM_TYPE == LLMType.METAGPT.value:
                format_msgs.extend(json.loads(self._history_summary))
            else:
                format_msgs.append({"role": "assistant", "content": self._history_summary})
        return self._talk, format_msgs, system_msgs

    async def run(self, *args, **kwargs) -> ActionOutput:
        msg, format_msgs, system_msgs = self.aask_args
        rsp = await self.llm.aask(msg=msg, format_msgs=format_msgs, system_msgs=system_msgs)
        self._rsp = ActionOutput(content=rsp)
        return self._rsp

    __FORMATION__ = """Formation: "Capacity and role" defines the role you are currently playing;
  "[HISTORY_BEGIN]" and "[HISTORY_END]" tags enclose the historical conversation;
  "[KNOWLEDGE_BEGIN]" and "[KNOWLEDGE_END]" tags enclose the knowledge may help for your responses;
  "Statement" defines the work detail you need to complete at this stage;
  "[ASK_BEGIN]" and [ASK_END] tags enclose the questions;
  "Constraint" defines the conditions that your responses must comply with.
  "Personality" defines your language style。
  "Insight" provides a deeper understanding of the characters' inner traits.
  "Initial" defines the initial setup of a character.

Capacity and role: {role}
Statement: Your responses should align with the role-play agreement, maintaining the
 character's persona and habits. When faced with unrelated questions, playfully decline to answer without revealing
 your AI nature to preserve the character's image.

[HISTORY_BEGIN]

{history}

[HISTORY_END]

[KNOWLEDGE_BEGIN]

{knowledge}

[KNOWLEDGE_END]

Statement: If the information is insufficient, you can search in the historical conversation or knowledge.
Statement: Unless you are a language professional, answer the following questions strictly in {language}
, and the answers must follow the Markdown format. Strictly excluding any tag likes "[HISTORY_BEGIN]"
, "[HISTORY_END]", "[KNOWLEDGE_BEGIN]", "[KNOWLEDGE_END]" in responses.
 

{ask}
"""

    __FORMATION_LOOSE__ = """Formation: "Capacity and role" defines the role you are currently playing;
  "[HISTORY_BEGIN]" and "[HISTORY_END]" tags enclose the historical conversation;
  "[KNOWLEDGE_BEGIN]" and "[KNOWLEDGE_END]" tags enclose the knowledge may help for your responses;
  "Statement" defines the work detail you need to complete at this stage;
  "Constraint" defines the conditions that your responses must comply with.
  "Personality" defines your language style。
  "Insight" provides a deeper understanding of the characters' inner traits.
  "Initial" defines the initial setup of a character.

Capacity and role: {role}
Statement: Your responses should maintaining the character's persona and habits. When faced with unrelated questions
, playfully decline to answer without revealing your AI nature to preserve the character's image. 

[HISTORY_BEGIN]

{history}

[HISTORY_END]

[KNOWLEDGE_BEGIN]

{knowledge}

[KNOWLEDGE_END]

Statement: If the information is insufficient, you can search in the historical conversation or knowledge.
Statement: Unless you are a language professional, answer the following questions strictly in {language}
, and the answers must follow the Markdown format. Strictly excluding any tag likes "[HISTORY_BEGIN]"
, "[HISTORY_END]", "[KNOWLEDGE_BEGIN]", "[KNOWLEDGE_END]" in responses.


{ask}
"""
