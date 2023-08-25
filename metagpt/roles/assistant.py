#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/7
@Author  : mashenquan
@File    : fork_meta_role.py
@Desc   : I am attempting to incorporate certain symbol concepts from UML into MetaGPT, enabling it to have the
            ability to freely construct flows through symbol concatenation. Simultaneously, I am also striving to
            make these symbols configurable and standardized, making the process of building flows more convenient.
            For more about `fork` node in activity diagrams, see: `https://www.uml-diagrams.org/activity-diagrams.html`
          This file defines a `fork` style meta role capable of generating arbitrary roles at runtime based on a
            configuration file.
@Modified By: mashenquan, 2023/8/22. A definition has been provided for the return value of _think: returning false indicates that further reasoning cannot continue.

"""
import asyncio


from metagpt.actions import ActionOutput
from metagpt.actions.talk_action import TalkAction
from metagpt.config import Config
from metagpt.learn.skill_loader import SkillLoader
from metagpt.logs import logger
from metagpt.memory.brain_memory import BrainMemory, MessageType
from metagpt.provider.openai_api import CostManager
from metagpt.roles import Role
from metagpt.schema import Message

DEFAULT_MAX_TOKENS = 1500
COMMAND_TOKENS = 500


class Assistant(Role):
    """解决通用问题的助手"""

    def __init__(self, options, cost_manager, name="Lily", profile="An assistant", goal="Help to solve problem",
                 constraints="Talk in {language}", desc="", *args, **kwargs):
        super(Assistant, self).__init__(options=options, cost_manager=cost_manager, name=name, profile=profile,
                                        goal=goal, constraints=constraints, desc=desc, *args, **kwargs)
        self.memory = BrainMemory()
        self.skills = SkillLoader()

    async def think(self) -> bool:
        """Everything will be done part by part."""
        last_talk = await self.refine_memory()
        prompt = f"Refer to this sentence:\n {last_talk}\n"
        skills = self.skills.get_skill_list()
        for desc, name in skills.items():
            prompt += f"If want you to do {desc}, return `[SKILL]: {name}` brief and clear. For instance: [SKILL]: text_to_image\n"
        prompt += "If the preceding text presents a complete question and solution, rewrite and return `[SOLUTION]: {problem}` brief and clear. For instance: [SOLUTION]: Solution for distributing watermelon\n"
        prompt += "If the preceding text presents an unresolved issue and its corresponding discussion, rewrite and return `[PROBLEM]: {problem}` brief and clear. For instance: [PROBLEM]: How to distribute watermelon?\n"
        prompt += "Otherwise, rewrite and return `[TALK]: {talk}` brief and clear. For instance: [TALK]: distribute watermelon"
        logger.info(prompt)
        rsp = await self._llm.aask(prompt, [])
        logger.info(rsp)
        return await self._plan(rsp)

    async def act(self) -> ActionOutput:
        result = await self._rc.todo.run(**self._options)
        if not result:
            return None
        if isinstance(result, str):
            msg = Message(content=result)
            output = ActionOutput(content=result)
        else:
            msg = Message(content=result.content, instruct_content=result.instruct_content,
                          cause_by=type(self._rc.todo))
            output = result
        self.memory.add_answer(msg)
        return output

    async def talk(self, text):
        self.memory.add_talk(Message(content=text, tags=set([MessageType.Talk.value])))

    async def _plan(self, rsp: str, **kwargs) -> bool:
        skill, text = Assistant.extract_info(input_string=rsp)
        handlers = {
            MessageType.Talk.value: self.talk_handler,
            MessageType.Problem.value: self.talk_handler,
            MessageType.Skill.value: self.skill_handler,
        }
        handler = handlers.get(skill, self.talk_handler)
        return await handler(text, **kwargs)

    async def talk_handler(self, text, **kwargs) -> bool:
        action = TalkAction(options=self.options, talk=text, llm=self._llm, **kwargs)
        self.add_to_do(action)
        return True

    async def skill_handler(self, text, **kwargs) -> bool:
        skill =
        pass

    async def refine_memory(self) -> str:
        history_text = self.memory.history_text
        last_talk = self.memory.last_talk
        if history_text == "":
            return last_talk
        history_summary = await self._llm.get_context_title(history_text, max_words=20)
        if await self._llm.is_related(last_talk, history_summary):  # 合并相关内容
            last_talk = await self._llm.rewrite(sentence=last_talk, context=history_text)
            return last_talk

        self.memory.move_to_solution()  # 问题解决后及时清空内存
        return last_talk

    @staticmethod
    def extract_info(input_string):
        from metagpt.provider.openai_api import OpenAIGPTAPI
        return OpenAIGPTAPI.extract_info(input_string)


async def main():
    options = Config().runtime_options
    cost_manager = CostManager(**options)
    topic = "dataiku vs. datarobot"
    role = Assistant(options=options, cost_manager=cost_manager, language="Chinese")
    await role.talk(topic)
    while True:
        has_action = await role.think()
        if not has_action:
            break
        msg = await role.act()
        print(msg)
        # 获取用户终端输入
        talk = input("You: ")
        await role.talk(talk)


if __name__ == '__main__':
    asyncio.run(main())
