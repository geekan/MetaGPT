# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 13:19:39
@Author  :   orange-crow
@File    :   write_code_v2.py
"""
from typing import Dict, List, Union

from metagpt.actions import Action
from metagpt.schema import Message


class WriteCode(Action):
    """Use openai function to generate code."""

    def __init__(self, name: str = "", context=None, llm=None) -> str:
        super().__init__(name, context, llm)

    def process_msg(self, prompt: Union[str, List[Dict], Message, List[Message]], system_msg: str = None):
        if isinstance(prompt, str):
            return system_msg + prompt if system_msg else prompt

        if isinstance(prompt, Message):
            prompt.content = system_msg + prompt.content if system_msg else prompt.content
            return prompt

        if isinstance(prompt, list) and system_msg:
            prompt.insert(0, {"role": "system", "content": system_msg})
        return prompt

    async def run(
        self, prompt: Union[str, List[Dict], Message, List[Message]], system_msg: str = None, **kwargs
    ) -> Dict:
        prompt = self.process_msg(prompt, system_msg)
        code_content = await self.llm.aask_code(prompt, **kwargs)
        return Message(content=code_content, role="assistant")
