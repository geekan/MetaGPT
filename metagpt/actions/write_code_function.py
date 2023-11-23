# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 13:19:39
@Author  :   orange-crow
@File    :   write_code_v2.py
"""
from typing import Dict, List, Union

from metagpt.actions import Action
from metagpt.schema import Message, Plan

class BaseWriteAnalysisCode(Action):

    async def run(self, context: List[Message], plan: Plan = None, task_guidance: str = ""):
        """Run of a code writing action, used in data analysis or modeling

        Args:
            context (List[Message]): Action output history, source action denoted by Message.cause_by
            plan (Plan, optional): Overall plan. Defaults to None.
            task_guidance (str, optional): suggested step breakdown for the current task. Defaults to "".
        """

class WriteCodeFunction(BaseWriteAnalysisCode):
    """Use openai function to generate code."""

    def __init__(self, name: str = "", context=None, llm=None) -> str:
        super().__init__(name, context, llm)

    def process_msg(self, prompt: Union[str, List[Dict], Message, List[Message]], system_msg: str = None):
        if isinstance(prompt, str):
            return system_msg + prompt if system_msg else prompt

        if isinstance(prompt, Message):
            if isinstance(prompt.content, dict):
                prompt.content = system_msg + str([(k, v) for k, v in prompt.content.items()])\
                    if system_msg else prompt.content
            else:
                prompt.content = system_msg + prompt.content if system_msg else prompt.content
            return prompt

        if isinstance(prompt, list):
            _prompt = []
            for msg in prompt:
                if isinstance(msg, Message) and isinstance(msg.content, dict):
                    msg.content = str([(k, v) for k, v in msg.content.items()])
                if isinstance(msg, Message):
                    msg = msg.to_dict()
                _prompt.append(msg)
            prompt = _prompt

        if isinstance(prompt, list) and system_msg:
            if system_msg not in prompt[0]['content']:
                prompt[0]['content'] = system_msg + prompt[0]['content']
        return prompt

    async def run(
        self, context: [List[Message]], plan: Plan = None, task_guidance: str = "", system_msg: str = None, **kwargs
    ) -> str:
        prompt = self.process_msg(context, system_msg)
        code_content = await self.llm.aask_code(prompt, **kwargs)
        return code_content
