#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/7
@Author  : mashenquan
@File    : assistant.py
@Desc   : I am attempting to incorporate certain symbol concepts from UML into MetaGPT, enabling it to have the
            ability to freely construct flows through symbol concatenation. Simultaneously, I am also striving to
            make these symbols configurable and standardized, making the process of building flows more convenient.
            For more about `fork` node in activity diagrams, see: `https://www.uml-diagrams.org/activity-diagrams.html`
          This file defines a `fork` style meta role capable of generating arbitrary roles at runtime based on a
            configuration file.
@Modified By: mashenquan, 2023/8/22. A definition has been provided for the return value of _think: returning false
            indicates that further reasoning cannot continue.

"""
import asyncio
from pathlib import Path

from metagpt.actions import ActionOutput
from metagpt.actions.skill_action import ArgumentsParingAction, SkillAction
from metagpt.actions.talk_action import TalkAction
from metagpt.config import CONFIG
from metagpt.learn.skill_loader import SkillLoader
from metagpt.logs import logger
from metagpt.memory.brain_memory import BrainMemory, MessageType
from metagpt.roles import Role
from metagpt.schema import Message


class Assistant(Role):
    """Assistant for solving common issues."""

    def __init__(
        self,
        name="Lily",
        profile="An assistant",
        goal="Help to solve problem",
        constraints="Talk in {language}",
        desc="",
        *args,
        **kwargs,
    ):
        super(Assistant, self).__init__(
            name=name, profile=profile, goal=goal, constraints=constraints, desc=desc, *args, **kwargs
        )
        brain_memory = CONFIG.BRAIN_MEMORY
        self.memory = BrainMemory(**brain_memory) if brain_memory else BrainMemory()
        skill_path = Path(CONFIG.SKILL_PATH) if CONFIG.SKILL_PATH else None
        self.skills = SkillLoader(skill_yaml_file_name=skill_path)

    async def think(self) -> bool:
        """Everything will be done part by part."""
        last_talk = await self.refine_memory()
        if not last_talk:
            return False
        prompt = ""
        skills = self.skills.get_skill_list()
        for desc, name in skills.items():
            prompt += f"If the text explicitly want you to {desc}, return `[SKILL]: {name}` brief and clear. For instance: [SKILL]: {name}\n"
        prompt += 'Otherwise, return `[TALK]: {talk}` brief and clear. For instance: if {talk} is "xxxx" return [TALK]: xxxx\n\n'
        prompt += f"Now what specific action is explicitly mentioned in the text: {last_talk}\n"
        logger.info(prompt)
        rsp = await self._llm.aask(prompt, [])
        logger.info(f"THINK: {prompt}\n, THINK RESULT: {rsp}\n")
        return await self._plan(rsp, last_talk=last_talk)

    async def act(self) -> ActionOutput:
        result = await self._rc.todo.run(**CONFIG.options)
        if not result:
            return None
        if isinstance(result, str):
            msg = Message(content=result)
            output = ActionOutput(content=result)
        else:
            msg = Message(
                content=result.content, instruct_content=result.instruct_content, cause_by=type(self._rc.todo)
            )
            output = result
        self.memory.add_answer(msg)
        return output

    async def talk(self, text):
        self.memory.add_talk(Message(content=text))

    async def _plan(self, rsp: str, **kwargs) -> bool:
        skill, text = Assistant.extract_info(input_string=rsp)
        handlers = {
            MessageType.Talk.value: self.talk_handler,
            MessageType.Skill.value: self.skill_handler,
        }
        handler = handlers.get(skill, self.talk_handler)
        return await handler(text, **kwargs)

    async def talk_handler(self, text, **kwargs) -> bool:
        history = self.memory.history_text
        action = TalkAction(
            talk=text, knowledge=self.memory.get_knowledge(), history_summary=history, llm=self._llm, **kwargs
        )
        self.add_to_do(action)
        return True

    async def skill_handler(self, text, **kwargs) -> bool:
        last_talk = kwargs.get("last_talk")
        skill = self.skills.get_skill(text)
        if not skill:
            logger.info(f"skill not found: {text}")
            return await self.talk_handler(text=last_talk, **kwargs)
        action = ArgumentsParingAction(skill=skill, llm=self._llm, **kwargs)
        await action.run(**kwargs)
        if action.args is None:
            return await self.talk_handler(text=last_talk, **kwargs)
        action = SkillAction(skill=skill, args=action.args, llm=self._llm, name=skill.name, desc=skill.description)
        self.add_to_do(action)
        return True

    async def refine_memory(self) -> str:
        history_text = self.memory.history_text
        last_talk = self.memory.pop_last_talk()
        if last_talk is None:  # No user feedback, unsure if past conversation is finished.
            return None
        if history_text == "":
            return last_talk
        history_summary = await self._llm.get_summary(history_text, max_words=800, keep_language=True)
        await self.memory.set_history_summary(
            history_summary=history_summary, redis_key=CONFIG.REDIS_KEY, redis_conf=CONFIG.REDIS
        )
        if last_talk and await self._llm.is_related(last_talk, history_summary):  # Merge relevant content.
            last_talk = await self._llm.rewrite(sentence=last_talk, context=history_text)
            return last_talk

        return last_talk

    @staticmethod
    def extract_info(input_string):
        from metagpt.provider.openai_api import OpenAIGPTAPI

        return OpenAIGPTAPI.extract_info(input_string)

    def get_memory(self) -> str:
        return self.memory.json()

    def load_memory(self, jsn):
        try:
            self.memory = BrainMemory(**jsn)
        except Exception as e:
            logger.exception(f"load error:{e}, data:{jsn}")


async def main():
    topic = "what's apple"
    role = Assistant(language="Chinese")
    await role.talk(topic)
    while True:
        has_action = await role.think()
        if not has_action:
            break
        msg = await role.act()
        logger.info(msg)
        # Retrieve user terminal input.
        logger.info("Enter prompt")
        talk = input("You: ")
        await role.talk(talk)


if __name__ == "__main__":
    CONFIG.language = "Chinese"
    asyncio.run(main())
