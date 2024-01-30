#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/8/7
# @Author  : mashenquan
# @File    : assistant.py
# @Desc   : I am attempting to incorporate certain symbol concepts from UML into MetaGPT, enabling it to have the
#             ability to freely construct flows through symbol concatenation. Simultaneously, I am also striving to
#             make these symbols configurable and standardized, making the process of building flows more convenient.
#             For more about `fork` node in activity diagrams, see: `https://www.uml-diagrams.org/activity-diagrams.html`
#           This file defines a `fork` style meta role capable of generating arbitrary roles at runtime based on a
#             configuration file.
# @Modified By: mashenquan, 2023/8/22. A definition has been provided for the return value of _think: returning false
#             indicates that further reasoning cannot continue.

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field

from metagpt.actions.skill_action import ArgumentsParingAction, SkillAction
from metagpt.actions.talk_action import TalkAction
from metagpt.learn.skill_loader import SkillsDeclaration
from metagpt.logs import logger
from metagpt.memory.brain_memory import BrainMemory
from metagpt.roles import Role
from metagpt.schema import Message


class MessageType(Enum):
    Talk = "TALK"
    Skill = "SKILL"


class Assistant(Role):
    """Assistant for solving common issues.

    Attributes:
        name: The name of the assistant.
        profile: A brief description of the assistant.
        goal: The goal of the assistant.
        constraints: Constraints that the assistant operates under.
        desc: Additional description of the assistant.
        memory: The memory component of the assistant.
        skills: The skills available to the assistant.
    """

    name: str = "Lily"
    profile: str = "An assistant"
    goal: str = "Help to solve problem"
    constraints: str = "Talk in {language}"
    desc: str = ""
    memory: BrainMemory = Field(default_factory=BrainMemory)
    skills: Optional[SkillsDeclaration] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        language = kwargs.get("language") or self.context.kwargs.language
        self.constraints = self.constraints.format(language=language)

    async def think(self) -> bool:
        """Processes the last interaction and decides on the next action.

        Returns:
            A boolean indicating if a valid action was determined.
        """
        last_talk = await self.refine_memory()
        if not last_talk:
            return False
        if not self.skills:
            skill_path = Path(self.context.kwargs.SKILL_PATH) if self.context.kwargs.SKILL_PATH else None
            self.skills = await SkillsDeclaration.load(skill_yaml_file_name=skill_path)

        prompt = ""
        skills = self.skills.get_skill_list(context=self.context)
        for desc, name in skills.items():
            prompt += f"If the text explicitly want you to {desc}, return `[SKILL]: {name}` brief and clear. For instance: [SKILL]: {name}\n"
        prompt += 'Otherwise, return `[TALK]: {talk}` brief and clear. For instance: if {talk} is "xxxx" return [TALK]: xxxx\n\n'
        prompt += f"Now what specific action is explicitly mentioned in the text: {last_talk}\n"
        rsp = await self.llm.aask(prompt, ["You are an action classifier"])
        logger.info(f"THINK: {prompt}\n, THINK RESULT: {rsp}\n")
        return await self._plan(rsp, last_talk=last_talk)

    async def act(self) -> Message:
        """Executes the determined action and returns a message.

        Returns:
            A message object containing the result of the action.
        """
        result = await self.rc.todo.run()
        if not result:
            return None
        if isinstance(result, str):
            msg = Message(content=result, role="assistant", cause_by=self.rc.todo)
        elif isinstance(result, Message):
            msg = result
        else:
            msg = Message(content=result.content, instruct_content=result.instruct_content, cause_by=type(self.rc.todo))
        self.memory.add_answer(msg)
        return msg

    async def talk(self, text):
        """Stores a talk action in the assistant's memory.

        Args:
            text: The text to be stored.
        """
        self.memory.add_talk(Message(content=text))

    async def _plan(self, rsp: str, **kwargs) -> bool:
        """Determines the appropriate handler based on the response and executes it.

        Args:
            rsp: The response string to plan actions for.

        Returns:
            A boolean indicating if the action was successfully planned and executed.
        """
        skill, text = BrainMemory.extract_info(input_string=rsp)
        handlers = {
            MessageType.Talk.value: self.talk_handler,
            MessageType.Skill.value: self.skill_handler,
        }
        handler = handlers.get(skill, self.talk_handler)
        return await handler(text, **kwargs)

    async def talk_handler(self, text, **kwargs) -> bool:
        """Handles talk actions.

        Args:
            text: The text to be processed in the talk action.

        Returns:
            A boolean indicating if the talk action was successfully handled.
        """
        history = self.memory.history_text
        text = kwargs.get("last_talk") or text
        self.set_todo(
            TalkAction(i_context=text, knowledge=self.memory.get_knowledge(), history_summary=history, llm=self.llm)
        )
        return True

    async def skill_handler(self, text, **kwargs) -> bool:
        """Handles skill actions.

        Args:
            text: The text to determine the skill action for.

        Returns:
            A boolean indicating if the skill action was successfully handled.
        """
        last_talk = kwargs.get("last_talk")
        skill = self.skills.get_skill(text)
        if not skill:
            logger.info(f"skill not found: {text}")
            return await self.talk_handler(text=last_talk, **kwargs)
        action = ArgumentsParingAction(skill=skill, llm=self.llm, ask=last_talk)
        await action.run(**kwargs)
        if action.args is None:
            return await self.talk_handler(text=last_talk, **kwargs)
        self.set_todo(SkillAction(skill=skill, args=action.args, llm=self.llm, name=skill.name, desc=skill.description))
        return True

    async def refine_memory(self) -> str:
        """Refines the assistant's memory by summarizing and rewriting if necessary.

        Returns:
            A string representing the refined memory or None if no refinement was possible.
        """
        last_talk = self.memory.pop_last_talk()
        if last_talk is None:  # No user feedback, unsure if past conversation is finished.
            return None
        if not self.memory.is_history_available:
            return last_talk
        history_summary = await self.memory.summarize(max_words=800, keep_language=True, llm=self.llm)
        if last_talk and await self.memory.is_related(text1=last_talk, text2=history_summary, llm=self.llm):
            # Merge relevant content.
            merged = await self.memory.rewrite(sentence=last_talk, context=history_summary, llm=self.llm)
            return f"{merged} {last_talk}"

        return last_talk

    def get_memory(self) -> str:
        """Dumps the assistant's memory model to a JSON string.

        Returns:
            A JSON string representation of the assistant's memory.
        """
        return self.memory.model_dump_json()

    def load_memory(self, m):
        """Loads the assistant's memory from a given object.

        Args:
            m: The memory object to load.
        """
        try:
            self.memory = BrainMemory(**m)
        except Exception as e:
            logger.exception(f"load error:{e}, data:{jsn}")
