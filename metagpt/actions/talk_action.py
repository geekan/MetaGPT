#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/28
@Author  : mashenquan
@File    : talk_action.py
@Desc    : Act as it’s a talk
"""

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.const import DEFAULT_LANGUAGE
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
    def prompt_old(self):
        prompt = ""
        if CONFIG.agent_description:
            prompt = (
                f"You are {CONFIG.agent_description}. Your responses should align with the role-play agreement, "
                f"maintaining the character's persona and habits. When faced with unrelated questions, playfully "
                f"decline to answer without revealing your AI nature to preserve the character's image.\n\n"
            )
        prompt += f"Background knowledge:\n{self._knowledge}\n\n" if self._knowledge else ""
        prompt += f"{self._history_summary}\n\n"
        if self._history_summary != "":
            prompt += "According to the historical conversation above, "
        language = CONFIG.language or DEFAULT_LANGUAGE
        prompt += (
            f"Answer the following questions in {language}, and the answers must follow the Markdown format.\n "
            f"{self._talk}"
        )
        return prompt

    @property
    def prompt(self):
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

    async def run(self, *args, **kwargs) -> ActionOutput:
        prompt = self.prompt
        logger.info(prompt)
        rsp = await self.llm.aask(msg=prompt, system_msgs=[])
        logger.info(rsp)
        self._rsp = ActionOutput(content=rsp)
        return self._rsp

    __FORMATION__ = """Formation: "Capacity and role" defines the role you are currently playing;
  "[HISTORY_BEGIN]" and "[HISTORY_END]" tags enclose the historical conversation;
  "[KNOWLEDGE_BEGIN]" and "[KNOWLEDGE_END]" tags enclose the knowledge may help for your responses;
  "Statement" defines the work detail you need to complete at this stage;
  "[ASK_BEGIN]" and [ASK_END] tags enclose the requirements for your to respond;
  "Constraint" defines the conditions that your responses must comply with.

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
Statement: Answer the following questions in {language}, and the answers must follow the Markdown format
 , excluding any tag likes "[HISTORY_BEGIN]", "[HISTORY_END]", "[KNOWLEDGE_BEGIN]", "[KNOWLEDGE_END]", "[ASK_BEGIN]"
 , "[ASK_END]" 
 
[ASK_BEGIN]
{ask}
[ASK_END]"""

    __FORMATION_LOOSE__ = """Formation: "Capacity and role" defines the role you are currently playing;
  "[HISTORY_BEGIN]" and "[HISTORY_END]" tags enclose the historical conversation;
  "[KNOWLEDGE_BEGIN]" and "[KNOWLEDGE_END]" tags enclose the knowledge may help for your responses;
  "Statement" defines the work detail you need to complete at this stage;
  "[ASK_BEGIN]" and [ASK_END] tags enclose the requirements for your to respond;
  "Constraint" defines the conditions that your responses must comply with.

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
Statement: Answer the following questions in {language}, and the answers must follow the Markdown format
 , excluding any tag likes "[HISTORY_BEGIN]", "[HISTORY_END]", "[KNOWLEDGE_BEGIN]", "[KNOWLEDGE_END]", "[ASK_BEGIN]"
 , "[ASK_END]" 

[ASK_BEGIN]
{ask}
[ASK_END]"""
