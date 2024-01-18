# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 13:19:39
@Author  :   orange-crow
@File    :   write_code_v2.py
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple, Union

from tenacity import retry, stop_after_attempt, wait_fixed

from metagpt.actions import Action
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.prompts.ml_engineer import (
    CODE_GENERATOR_WITH_TOOLS,
    GENERATE_CODE_PROMPT,
    ML_TOOL_USAGE_PROMPT,
    SELECT_FUNCTION_TOOLS,
    TOOL_RECOMMENDATION_PROMPT,
    TOOL_USAGE_PROMPT,
)
from metagpt.schema import Message, Plan
from metagpt.tools.tool_registry import TOOL_REGISTRY
from metagpt.utils.common import create_func_config, remove_comments


class BaseWriteAnalysisCode(Action):
    DEFAULT_SYSTEM_MSG: str = """You are Code Interpreter, a world-class programmer that can complete any goal by executing code. Strictly follow the plan and generate code step by step. Each step of the code will be executed on the user's machine, and the user will provide the code execution results to you.**Notice: The code for the next step depends on the code for the previous step. Must reuse variables in the lastest other code directly, dont creat it again, it is very import for you. Use !pip install in a standalone block to install missing packages.Usually the libraries you need are already installed.Dont check if packages already imported.**"""  # prompt reference: https://github.com/KillianLucas/open-interpreter/blob/v0.1.4/interpreter/system_message.txt
    # REUSE_CODE_INSTRUCTION = """ATTENTION: DONT include codes from previous tasks in your current code block, include new codes only, DONT repeat codes!"""

    def process_msg(self, prompt: Union[str, List[Dict], Message, List[Message]], system_msg: str = None):
        default_system_msg = system_msg or self.DEFAULT_SYSTEM_MSG
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
        if default_system_msg not in messages[0]["content"] and messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": default_system_msg})
        elif default_system_msg not in messages[0]["content"] and messages[0]["role"] == "system":
            messages[0] = {
                "role": "system",
                "content": messages[0]["content"] + default_system_msg,
            }
        return messages

    async def run(self, context: List[Message], plan: Plan = None) -> dict:
        """Run of a code writing action, used in data analysis or modeling

        Args:
            context (List[Message]): Action output history, source action denoted by Message.cause_by
            plan (Plan, optional): Overall plan. Defaults to None.

        Returns:
            dict: code result in the format of {"code": "print('hello world')", "language": "python"}
        """


class WriteCodeByGenerate(BaseWriteAnalysisCode):
    """Write code fully by generation"""

    async def run(
        self,
        context: [List[Message]],
        plan: Plan = None,
        system_msg: str = None,
        **kwargs,
    ) -> dict:
        # context.append(Message(content=self.REUSE_CODE_INSTRUCTION, role="user"))
        prompt = self.process_msg(context, system_msg)
        code_content = await self.llm.aask_code(prompt, **kwargs)
        return code_content


class WriteCodeWithTools(BaseWriteAnalysisCode):
    """Write code with help of local available tools. Choose tools first, then generate code to use the tools"""

    available_tools: dict = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _parse_recommend_tools(self, recommend_tools: list) -> dict:
        """
        Parses and validates a list of recommended tools, and retrieves their schema from registry.

        Args:
            recommend_tools (list): A list of recommended tools.

        Returns:
            dict: A dict of valid tool schemas.
        """
        valid_tools = []
        for tool_name in recommend_tools:
            if TOOL_REGISTRY.has_tool(tool_name):
                valid_tools.append(TOOL_REGISTRY.get_tool(tool_name))

        tool_catalog = {tool.name: tool.schemas for tool in valid_tools}
        return tool_catalog

    async def _tool_recommendation(
        self,
        task: str,
        code_steps: str,
        available_tools: dict,
    ) -> list:
        """
        Recommend tools for the specified task.

        Args:
            task (str): the task to recommend tools for
            code_steps (str): the code steps to generate the full code for the task
            available_tools (dict): the available tools description

        Returns:
            list: recommended tools for the specified task
        """
        prompt = TOOL_RECOMMENDATION_PROMPT.format(
            current_task=task,
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
        **kwargs,
    ) -> str:
        tool_type = (
            plan.current_task.task_type
        )  # find tool type from task type through exact match, can extend to retrieval in the future
        available_tools = TOOL_REGISTRY.get_tools_by_type(tool_type)
        special_prompt = (
            TOOL_REGISTRY.get_tool_type(tool_type).usage_prompt if TOOL_REGISTRY.has_tool_type(tool_type) else ""
        )
        code_steps = plan.current_task.code_steps

        tool_catalog = {}

        if available_tools:
            available_tools = {tool_name: tool.schemas["description"] for tool_name, tool in available_tools.items()}

            recommend_tools = await self._tool_recommendation(
                plan.current_task.instruction, code_steps, available_tools
            )
            tool_catalog = self._parse_recommend_tools(recommend_tools)
            logger.info(f"Recommended tools: \n{recommend_tools}")

        tools_instruction = TOOL_USAGE_PROMPT.format(special_prompt=special_prompt, tool_catalog=tool_catalog)

        context.append(Message(content=tools_instruction, role="user"))

        prompt = self.process_msg(context)

        tool_config = create_func_config(CODE_GENERATOR_WITH_TOOLS)
        rsp = await self.llm.aask_code(prompt, **tool_config)
        return rsp


class WriteCodeWithToolsML(WriteCodeWithTools):
    async def run(
        self,
        context: List[Message],
        plan: Plan = None,
        column_info: str = "",
        **kwargs,
    ) -> Tuple[List[Message], str]:
        tool_type = (
            plan.current_task.task_type
        )  # find tool type from task type through exact match, can extend to retrieval in the future
        available_tools = TOOL_REGISTRY.get_tools_by_type(tool_type)
        special_prompt = (
            TOOL_REGISTRY.get_tool_type(tool_type).usage_prompt if TOOL_REGISTRY.has_tool_type(tool_type) else ""
        )
        code_steps = plan.current_task.code_steps

        finished_tasks = plan.get_finished_tasks()
        code_context = [remove_comments(task.code) for task in finished_tasks]
        code_context = "\n\n".join(code_context)

        if available_tools:
            available_tools = {tool_name: tool.schemas["description"] for tool_name, tool in available_tools.items()}

            recommend_tools = await self._tool_recommendation(
                plan.current_task.instruction, code_steps, available_tools
            )
            tool_catalog = self._parse_recommend_tools(recommend_tools)
            logger.info(f"Recommended tools: \n{recommend_tools}")

            prompt = ML_TOOL_USAGE_PROMPT.format(
                user_requirement=plan.goal,
                history_code=code_context,
                current_task=plan.current_task.instruction,
                column_info=column_info,
                special_prompt=special_prompt,
                code_steps=code_steps,
                tool_catalog=tool_catalog,
            )

        else:
            prompt = GENERATE_CODE_PROMPT.format(
                user_requirement=plan.goal,
                history_code=code_context,
                current_task=plan.current_task.instruction,
                column_info=column_info,
                special_prompt=special_prompt,
                code_steps=code_steps,
            )

        tool_config = create_func_config(CODE_GENERATOR_WITH_TOOLS)
        rsp = await self.llm.aask_code(prompt, **tool_config)
        context = [Message(content=prompt, role="user")]
        return context, rsp


class MakeTools(WriteCodeByGenerate):
    DEFAULT_SYSTEM_MSG: str = """Convert any codes provied for you to a very General Function Code startswith `def`.\n
    **Notice:
    1. Your code must contain a general function start with `def`.
    2. Refactor your code to get the most efficient implementation for large input data in the shortest amount of time.
    3. Must use Google style for function docstring, and your docstring must be consistent with the code,without missing anything.
    4. Write example code after `if __name__ == '__main__':`by using old varibales in old code,
    and make sure it could be execute in the user's machine.
    5. Only use the imported packages**
    """

    def __init__(self, name: str = "", context: list[Message] = None, llm: LLM = None, workspace: str = None):
        """
        :param str name: name, defaults to ''
        :param list[Message] context: context, defaults to None
        :param LLM llm: llm, defaults to None
        :param str workspace: tools code saved file path dir, defaults to None
        """
        super().__init__(name, context, llm)
        self.workspace = workspace or str(Path(__file__).parents[1].joinpath("./tools/functions/libs/udf"))
        self.file_suffix: str = ".py"
        self.context = []

    def parse_function_name(self, function_code: str) -> str:
        # 定义正则表达式模式
        pattern = r"\bdef\s+([a-zA-Z_]\w*)\s*\("
        # 在代码中搜索匹配的模式
        match = re.search(pattern, function_code)
        # 如果找到匹配项，则返回匹配的函数名；否则返回None
        if match:
            return match.group(1)
        else:
            return None

    def save(self, tool_code: str) -> None:
        func_name = self.parse_function_name(tool_code)
        if func_name is None:
            raise ValueError(f"No function name found in {tool_code}")
        saved_path = Path(self.workspace).joinpath(func_name + self.file_suffix)
        logger.info(f"Saved tool_code {func_name} in {str(saved_path)}.")
        saved_path.write_text(tool_code, encoding="utf-8")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def run(self, code: Union[str, List[dict]], code_desc: str = None, **kwargs) -> str:
        # 拼接code prompt
        code_prompt = f"The following code is about {code_desc}, convert it to be a General Function, {code}"
        if not self.context:
            self.context = self.process_msg(code_prompt)
        else:
            self.context.append(self.process_msg(code_prompt)[-1])
        logger.info(f"\n\nAsk to Make tools:\n{'-'*60}\n {self.context[-1]}")

        # 更新kwargs
        if "code" in kwargs:
            kwargs.pop("code")
        if "code_desc" in kwargs:
            kwargs.pop("code_desc")

        max_tries, current_try = 3, 0
        while True:
            tool_code = await self.llm.aask_code(self.context, **kwargs)
            func_name = self.parse_function_name(tool_code["code"])
            current_try += 1
            # make tools failed, add error message to context.
            if not func_name:
                logger.info(f"\n\nTools Respond\n{'-'*60}\n: {tool_code}")
                logger.error(f"No function name found in code, we will retry make tools.\n{tool_code['code']}\n")
                self.context.append(
                    {"role": "user", "content": "We need a general function in above code,but not found function."}
                )
            # end make tools
            if func_name is not None or current_try >= max_tries:
                if current_try >= max_tries:
                    logger.error(
                        f"We have tried the maximum number of attempts {max_tries}\
                    and still have not created tools successfully, we will skip it."
                    )
                break
        logger.info(f"\n\nTools Respond\n{'-'*60}\n: {tool_code}")
        self.save(tool_code["code"])
        return tool_code["code"]
