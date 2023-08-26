from enum import Enum
from typing import List

import pydantic

from metagpt import Message

class MessageType(Enum):
    Talk = "TALK"
    Solution = "SOLUTION"
    Problem = "PROBLEM"
    Skill = "SKILL"
    Answer = "ANSWER"


class BrainMemory(pydantic.BaseModel):
    history: List[Message] = []
    stack: List[Message] = []
    solution: List[Message] = []


    def add_talk(self, msg: Message):
        msg.add_tag(MessageType.Talk.value)
        self.history.append(msg)

    def add_answer(self, msg: Message):
        msg.add_tag(MessageType.Answer.value)
        self.history.append(msg)

    @property
    def history_text(self):
        if len(self.history) == 0:
            return ""
        texts = [m.content for m in self.history[:-1]]
        return "\n".join(texts)

    def move_to_solution(self):
        if len(self.history) < 2:
            return
        msgs = self.history[:-1]
        self.solution.extend(msgs)
        if not self.history[-1].is_contain(MessageType.Talk.value):
            self.solution.append(self.history[-1])
            self.history = []
        else:
            self.history = self.history[-1:]

    @property
    def last_talk(self):
        if len(self.history) == 0 or not self.history[-1].is_contain_tags([MessageType.Talk.value]):
            return ""
        return self.history[-1].content

