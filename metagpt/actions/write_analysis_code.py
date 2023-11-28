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

    async def run(self, context: List[Message], plan: Plan = None, task_guide: str = "") -> str:
        """Run of a code writing action, used in data analysis or modeling

        Args:
            context (List[Message]): Action output history, source action denoted by Message.cause_by
            plan (Plan, optional): Overall plan. Defaults to None.
            task_guide (str, optional): suggested step breakdown for the current task. Defaults to "".
        
        Returns:
            str: The code string.
        """

class WriteCodeByGenerate(BaseWriteAnalysisCode):
    """Write code fully by generation"""

    def __init__(self, name: str = "", context=None, llm=None) -> str:
        super().__init__(name, context, llm)

    def process_msg(self, prompt: Union[str, List[Dict], Message, List[Message]], system_msg: str = None):
        default_system_msg = """You are Code Interpreter, a world-class programmer that can complete any goal by executing code. Strictly follow the plan and generate code step by step. Each step of the code will be executed on the user's machine, and the user will provide the code execution results to you.**Notice: The code for the next step depends on the code for the previous step. Reuse existing code directly. Use !pip install to install missing packages.**"""
        # 全部转成list
        if not isinstance(prompt, list):
            prompt = [prompt]
        assert isinstance(prompt, list)
        # 转成list[dict]
        messages = []
        for p in prompt:
            if isinstance(p, str):
                messages.append({'role': 'user', 'content': p})
            elif isinstance(p, dict):
                messages.append(p)
            elif isinstance(p, Message):
                if isinstance(p.content, str):
                    messages.append(p.to_dict())
                elif isinstance(p.content, dict) and 'code' in p.content:
                    messages.append(p.content['code'])

        # 添加默认的提示词
        if default_system_msg not in messages[0]['content'] and messages[0]['role'] != 'system':
            messages.insert(0, {'role': 'system', 'content': default_system_msg})
        elif default_system_msg not in messages[0]['content'] and messages[0]['role'] == 'system':
            messages[0] = {'role': 'system', 'content': messages[0]['content']+default_system_msg}
        return messages

    async def run(
        self, context: [List[Message]], plan: Plan = None, task_guide: str = "", system_msg: str = None, **kwargs
    ) -> str:
        prompt = self.process_msg(context, system_msg)
        code_content = await self.llm.aask_code(prompt, **kwargs)
        return code_content["code"]


class WriteCodeWithTools(BaseWriteAnalysisCode):
    """Write code with help of local available tools. Choose tools first, then generate code to use the tools"""

    async def run(self, context: List[Message], plan: Plan = None, task_guide: str = "") -> str:
        return "print('abc')"
