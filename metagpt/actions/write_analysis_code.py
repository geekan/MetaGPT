# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 13:19:39
@Author  :   orange-crow
@File    :   write_code_v2.py
"""
import json
from typing import Dict, List, Union

from metagpt.actions import Action
from metagpt.prompts.ml_engineer import (
    TOOL_RECOMMENDATION_PROMPT,
    SELECT_FUNCTION_TOOLS,
    CODE_GENERATOR_WITH_TOOLS,
    TOO_ORGANIZATION_PROMPT,
    ML_SPECIFIC_PROMPT,
    ML_MODULE_MAP,
    TOOL_OUTPUT_DESC,
)
from metagpt.schema import Message, Plan
from metagpt.tools.functions import registry
from metagpt.utils.common import create_func_config


class BaseWriteAnalysisCode(Action):
    async def run(
        self, context: List[Message], plan: Plan = None, task_guide: str = ""
    ) -> str:
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

    def process_msg(
        self,
        prompt: Union[str, List[Dict], Message, List[Message]],
        system_msg: str = None,
    ):
        default_system_msg = """You are Open Interpreter, a world-class programmer that can complete any goal by executing code. Strictly follow the plan and generate code step by step. Each step of the code will be executed on the user's machine, and the user will provide the code execution results to you.**Notice: The code for the next step depends on the code for the previous step.**"""
        # 全部转成list
        if not isinstance(prompt, list):
            prompt = [prompt]
        assert isinstance(prompt, list)
        # 转成list[dict]
        messages = []
        for p in prompt:
            if isinstance(p, str):
                messages.append({"role": "user", "content": p})
            elif isinstance(p, dict):
                messages.append(p)
            elif isinstance(p, Message):
                if isinstance(p.content, str):
                    messages.append(p.to_dict())
                elif isinstance(p.content, dict) and "code" in p.content:
                    messages.append(p.content["code"])

        # 添加默认的提示词
        if (
            default_system_msg not in messages[0]["content"]
            and messages[0]["role"] != "system"
        ):
            messages.insert(0, {"role": "system", "content": default_system_msg})
        elif (
            default_system_msg not in messages[0]["content"]
            and messages[0]["role"] == "system"
        ):
            messages[0] = {
                "role": "system",
                "content": messages[0]["content"] + default_system_msg,
            }
        return messages

    async def run(
        self,
        context: [List[Message]],
        plan: Plan = None,
        task_guide: str = "",
        system_msg: str = None,
        **kwargs,
    ) -> str:
        prompt = self.process_msg(context, system_msg)
        code_content = await self.llm.aask_code(prompt, **kwargs)
        return code_content["code"]


class WriteCodeWithTools(BaseWriteAnalysisCode):
    """Write code with help of local available tools. Choose tools first, then generate code to use the tools"""

    @staticmethod
    def _parse_recommend_tools(module: str, recommend_tools: list) -> str:
        """
        Converts recommended tools to a JSON string and checks tool availability in the registry.

        Args:
            module (str): The module name for querying tools in the registry.
            recommend_tools (list): A list of lists of recommended tools for each step.

        Returns:
            str: A JSON string with available tools and their schemas for each step.
        """
        valid_tools = {}
        available_tools = registry.get_all_by_module(module).keys()
        for index, tools in enumerate(recommend_tools):
            key = f"Step {index + 1}"
            tools = [tool for tool in tools if tool in available_tools]
            valid_tools[key] = registry.get_schemas(module, tools)
        return json.dumps(valid_tools)

    async def _tool_recommendation(
        self, task: str, data_desc: str, code_steps: str, available_tools: list
    ) -> list:
        """
        Recommend tools for each step of the specified task

        Args:
            task (str): the task description
            data_desc (str): the description of the dataset for the task
            code_steps (str): the code steps to generate the full code for the task
            available_tools (list): the available tools for the task

        Returns:
            list: recommended tools for each step of the specified task
        """
        prompt = TOOL_RECOMMENDATION_PROMPT.format(
            task=task,
            data_desc=data_desc,
            code_steps=code_steps,
            available_tools=available_tools,
        )
        tool_config = create_func_config(SELECT_FUNCTION_TOOLS)
        rsp = await self.llm.aask_code(prompt, **tool_config)
        recommend_tools = rsp["recommend_tools"]
        return recommend_tools

    async def run(
        self,
        context: List[Message],
        plan: Plan = None,
        task_guide: str = "",
        data_desc: str = "",
    ) -> str:
        task_type = plan.current_task.task_type
        task = plan.current_task.instruction
        available_tools = registry.get_all_schema_by_module(task_type)
        available_tools = [
            {k: tool[k] for k in ["name", "description"] if k in tool}
            for tool in available_tools
        ]
        task_guide = "\n".join(
            [f"Step {step.strip()}" for step in task_guide.split("\n")]
        )

        recommend_tools = await self._tool_recommendation(
            task, task_guide, available_tools
        )
        recommend_tools = self._parse_recommend_tools(task_type, recommend_tools)

        special_prompt = ML_SPECIFIC_PROMPT.get(task_type, "")
        module_name = ML_MODULE_MAP[task_type]
        output_desc = TOOL_OUTPUT_DESC.get(task_type, "")
        all_tasks = ""
        completed_code = ""

        for i, task in enumerate(plan.tasks):
            stats = "DONE" if task.is_finished else "TODO"
            all_tasks += f"Subtask {task.task_id}: {task.instruction}({stats})\n"

        for task in plan.tasks:
            if task.code:
                completed_code += task.code + "\n"

        prompt = TOO_ORGANIZATION_PROMPT.format(
            all_tasks=all_tasks,
            completed_code=completed_code,
            data_desc=data_desc,
            special_prompt=special_prompt,
            code_steps=task_guide,
            module_name=module_name,
            output_desc=output_desc,
            available_tools=recommend_tools,
        )
        tool_config = create_func_config(CODE_GENERATOR_WITH_TOOLS)
        rsp = await self.llm.aask_code(prompt, **tool_config)
        return rsp["code"]
