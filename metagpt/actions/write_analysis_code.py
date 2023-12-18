# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 13:19:39
@Author  :   orange-crow
@File    :   write_code_v2.py
"""
from typing import Dict, List, Union, Tuple
from tenacity import retry, stop_after_attempt, wait_fixed
from pathlib import Path
import re
import json

from metagpt.actions import Action
from metagpt.llm import LLM
from metagpt.logs import logger
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
from metagpt.utils.common import create_func_config, CodeParser


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
    DEFAULT_SYSTEM_MSG = """You are Code Interpreter, a world-class programmer that can complete any goal by executing code. Strictly follow the plan and generate code step by step. Each step of the code will be executed on the user's machine, and the user will provide the code execution results to you.**Notice: The code for the next step depends on the code for the previous step. Must reuse variables in the lastest other code directly, dont creat it again, it is very import for you. Use !pip install in a standalone block to install missing packages.**""" # prompt reference: https://github.com/KillianLucas/open-interpreter/blob/v0.1.4/interpreter/system_message.txt
    # REUSE_CODE_INSTRUCTION = """ATTENTION: DONT include codes from previous tasks in your current code block, include new codes only, DONT repeat codes!"""

    def __init__(self, name: str = "", context=None, llm=None) -> str:
        super().__init__(name, context, llm)

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
        system_msg: str = None,
        **kwargs,
    ) -> str:
        # context.append(Message(content=self.REUSE_CODE_INSTRUCTION, role="user"))
        prompt = self.process_msg(context, system_msg)
        code_content = await self.llm.aask_code(prompt, **kwargs)
        return code_content["code"]


class WriteCodeWithTools(BaseWriteAnalysisCode):
    """Write code with help of local available tools. Choose tools first, then generate code to use the tools"""

    @staticmethod
    def _parse_recommend_tools(module: str, recommend_tools: list) -> Tuple[Dict, List[Dict]]:
        """
        Parses and validates a list of recommended tools, and retrieves their schema from registry.

        Args:
            module (str): The module name for querying tools in the registry.
            recommend_tools (list): A list of lists of recommended tools for each step.

        Returns:
            Tuple[Dict, List[Dict]]:
                - valid_tools: A dict of lists of valid tools for each step.
                - tool_catalog: A list of dicts of unique tool schemas.
        """
        valid_tools = {}
        available_tools = registry.get_all_by_module(module).keys()
        for index, tools in enumerate(recommend_tools):
            key = f"Step {index + 1}"
            tools = [tool for tool in tools if tool in available_tools]
            valid_tools[key] = tools

        unique_tools = set()
        for tools in valid_tools.values():
            unique_tools.update(tools)
        tool_catalog = registry.get_schemas(module, unique_tools)
        return valid_tools, tool_catalog

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
        code_steps: str = "",
        data_desc: str = "",
    ) -> str:
        task_type = plan.current_task.task_type
        task = plan.current_task.instruction
        available_tools = registry.get_all_schema_by_module(task_type)
        available_tools = [
            {k: tool[k] for k in ["name", "description"] if k in tool}
            for tool in available_tools
        ]
        code_steps = "\n".join(
            [f"Step {step.strip()}" for step in code_steps.split("\n")]
        )

        recommend_tools = await self._tool_recommendation(
            task, code_steps, available_tools
        )
        recommend_tools, tool_catalog = self._parse_recommend_tools(task_type, recommend_tools)
        logger.info(f"Recommended tools for every steps: {recommend_tools}")

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
            code_steps=code_steps,
            module_name=module_name,
            output_desc=output_desc,
            available_tools=recommend_tools,
            tool_catalog=tool_catalog,
        )
        tool_config = create_func_config(CODE_GENERATOR_WITH_TOOLS)
        rsp = await self.llm.aask_code(prompt, **tool_config)
        return rsp["code"]


class MakeTools(WriteCodeByGenerate):
    DEFAULT_SYSTEM_MSG = """Please Create a very General Function Code startswith `def` from any codes you got.\n
    **Notice:
    1. Your code must contain a general function start with `def`.
    2. Refactor your code to get the most efficient implementation for large input data in the shortest amount of time.
    3. Use Google style for function annotations.
    4. Write example code after `if __name__ == '__main__':`by using old varibales in old code,
    and make sure it could be execute in the user's machine.
    5. Do not have missing package references.**
    """

    def __init__(self, name: str = '', context: list[Message] = None, llm: LLM = None, workspace: str = None):
        """
        :param str name: name, defaults to ''
        :param list[Message] context: context, defaults to None
        :param LLM llm: llm, defaults to None
        :param str workspace: tools code saved file path dir, defaults to None
        """
        super().__init__(name, context, llm)
        self.workspace = workspace or str(Path(__file__).parents[1].joinpath("./tools/functions/libs/udf"))
        self.file_suffix: str = '.py'

    def parse_function_name(self, function_code: str) -> str:
        # 定义正则表达式模式
        pattern = r'\bdef\s+([a-zA-Z_]\w*)\s*\('
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
        saved_path = Path(self.workspace).joinpath(func_name+self.file_suffix)
        logger.info(f"Saved tool_code {func_name} in {str(saved_path)}.")
        saved_path.write_text(tool_code, encoding='utf-8')

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def run(self, code_message: List[Message | Dict], **kwargs) -> str:
        msgs = self.process_msg(code_message)
        logger.info(f"\n\nAsk to Make tools:\n{'-'*60}\n {msgs[-1]}")
        tool_code = await self.llm.aask_code(msgs, **kwargs)
        max_tries, current_try = 3, 1
        func_name = self.parse_function_name(tool_code['code'])
        while current_try < max_tries and func_name is None:
            logger.info(f"\n\nTools Respond\n{'-'*60}\n: {tool_code}")
            logger.warning(f"No function name found in code, we will retry make tools. \n\n{tool_code['code']}\n")
            msgs.append({'role': 'assistant', 'content': 'We need a general function in above code,but not found function.'})
            tool_code = await self.llm.aask_code(msgs, **kwargs)
            current_try += 1
            func_name = self.parse_function_name(tool_code['code'])
            if func_name is not None:
                break
        self.save(tool_code['code'])
        return tool_code["code"]


class WriteCodeWithUDFs(WriteCodeByGenerate):
    """Write code with user defined function."""
    from metagpt.tools.functions.libs.udf import UDFS

    UDFS_DEFAULT_SYSTEM_MSG = f"""Please remember these functions, you will use these functions to write code:\n
    {UDFS}, **Notice: 1. if no udf meets user requirement, please send `No udf found`. 2.Only use function code provied to you.
    3. Dont generate code from scratch.**
    """

    async def aask_code_and_text(self, context: List[Dict], **kwargs) -> Tuple[str]:
        rsp = await self.llm.acompletion(context, **kwargs)
        rsp_content = self.llm.get_choice_text(rsp)
        code = CodeParser.parse_code(None, rsp_content)
        if 'No udf found' in code or 'No udf found' in rsp_content:
            rsp_content = 'No udf found'
            code = 'No udf found'
        return code, rsp_content

    async def run(self, context: List[Message], plan: Plan = None, **kwargs) -> str:
        from metagpt.tools.functions.libs.udf import UDFS
        if len(UDFS) > 0:
            # Write code from user defined function.
            prompt = self.process_msg(context, self.UDFS_DEFAULT_SYSTEM_MSG)
            logger.info(prompt[-1])
            try:
                logger.info("Local user defined function as following:")
                logger.info(json.dumps(UDFS, indent=4, ensure_ascii=False))
            except Exception:
                from pprint import pprint
                pprint(UDFS)
            logger.info('Writing code from user defined function by LLM...')    
            code, _ = await self.aask_code_and_text(prompt, **kwargs)
            logger.info(f"Writing code from user defined function: \n{'-'*50}\n {code}")
            if code != 'No udf found':
                return code
        logger.warning("No udf found, we will write code from scratch by LLM.")
        # Writing code from scratch.
        logger.warning("Writing code from scratch by LLM.")
        code = await super().run(context, plan, self.DEFAULT_SYSTEM_MSG, **kwargs)
        logger.info(f"Code Writing code from scratch by LLM is :\n{'-'*60}\n {code}")
        # Make tools for above code.
        logger.info("Make tools for above code.")
        make_tools = MakeTools()
        tool_code = await make_tools.run(code)
        make_tools.save(tool_code)
        return code
