#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : brain_memory.py
@Desc    : Support memory for multiple tasks and multiple mainlines.
"""

from enum import Enum
from typing import Dict, List

import pydantic

from metagpt import Message


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
        texts = [Message(**m).content for m in self.history[:-1]]
        return "\n".join(texts)

    def move_to_solution(self, history_summary):
        """放入solution队列，以备后续长程检索。目前还未加此功能，先用history_summary顶替"""
        if len(self.history) < 2:
            return
        msgs = self.history[:-1]
        self.solution.extend(msgs)
        if not Message(**self.history[-1]).is_contain(MessageType.Talk.value):
            self.solution.append(self.history[-1])
            self.history = []
        else:
            self.history = self.history[-1:]
        self.history.insert(0, Message(content="RESOLVED: " + history_summary))

    @property
    def last_talk(self):
        if len(self.history) == 0:
            return None
        last_msg = Message(**self.history[-1])
        if not last_msg.is_contain(MessageType.Talk.value):
            return None
        return last_msg.content
