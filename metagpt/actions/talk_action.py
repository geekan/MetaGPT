#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/28
@Author  : mashenquan
@File    : talk_action.py
@Desc    : Act as it’s a talk
"""
from typing import Optional

from metagpt.actions import Action
from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.schema import Message


class TalkAction(Action):
    i_context: str
    history_summary: str = ""
    knowledge: str = ""
    rsp: Optional[Message] = None

    @property
    def agent_description(self):
        return self.context.kwargs.agent_description

    @property
    def language(self):
        return self.context.kwargs.language or config.language

    @property
    def prompt(self):
        prompt = ""
        if self.agent_description:
            prompt = (
                f"You are {self.agent_description}. Your responses should align with the role-play agreement, "
                f"maintaining the character's persona and habits. When faced with unrelated questions, playfully "
                f"decline to answer without revealing your AI nature to preserve the character's image.\n\n"
            )
        prompt += f"Knowledge:\n{self.knowledge}\n\n" if self.knowledge else ""
        prompt += f"{self.history_summary}\n\n"
        prompt += (
            "If the information is insufficient, you can search in the historical conversation or knowledge above.\n"
        )
        language = self.language
        prompt += (
            f"Answer the following questions strictly in {language}, and the answers must follow the Markdown format.\n "
            f"{self.i_context}"
        )
        logger.debug(f"PROMPT: {prompt}")
        return prompt

    @property
    def prompt_gpt4(self):
        kvs = {
            "{role}": self.agent_description or "",
            "{history}": self.history_summary or "",
            "{knowledge}": self.knowledge or "",
            "{language}": self.language,
            "{ask}": self.i_context,
        }
        prompt = TalkActionPrompt.FORMATION_LOOSE
        for k, v in kvs.items():
            prompt = prompt.replace(k, v)
        logger.info(f"PROMPT: {prompt}")
        return prompt

    # async def run_old(self, *args, **kwargs) -> ActionOutput:
    #     prompt = self.prompt
    #     rsp = await self.llm.aask(msg=prompt, system_msgs=[])
    #     logger.debug(f"PROMPT:{prompt}\nRESULT:{rsp}\n")
    #     self._rsp = ActionOutput(content=rsp)
    #     return self._rsp

    @property
    def aask_args(self):
        language = self.language
        system_msgs = [
            f"You are {self.agent_description}.",
            "Your responses should align with the role-play agreement, "
            "maintaining the character's persona and habits. When faced with unrelated questions, playfully "
            "decline to answer without revealing your AI nature to preserve the character's image.",
            "If the information is insufficient, you can search in the context or knowledge.",
            f"Answer the following questions strictly in {language}, and the answers must follow the Markdown format.",
        ]
        format_msgs = []
        if self.knowledge:
            format_msgs.append({"role": "assistant", "content": self.knowledge})
        if self.history_summary:
            format_msgs.append({"role": "assistant", "content": self.history_summary})
        return self.i_context, format_msgs, system_msgs

    async def run(self, with_message=None, **kwargs) -> Message:
        msg, format_msgs, system_msgs = self.aask_args
        rsp = await self.llm.aask(msg=msg, format_msgs=format_msgs, system_msgs=system_msgs, stream=False)
        self.rsp = Message(content=rsp, role="assistant", cause_by=self)
        return self.rsp


class TalkActionPrompt:
    FORMATION = """Formation: "Capacity and role" defines the role you are currently playing;
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

    FORMATION_LOOSE = """Formation: "Capacity and role" defines the role you are currently playing;
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
