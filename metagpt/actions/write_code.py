#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code.py
"""
from metagpt.actions import WriteDesign
from metagpt.actions.action import Action
from metagpt.actions.task import Task
from metagpt.strategy.cot import ChainOfThoughtForEngineer as COT
from metagpt.strategy.tot import TreeOfThoughtForEngineer as TOT
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from tenacity import retry, stop_after_attempt, wait_fixed
from metagpt.config import CONFIG
from metagpt.roles.prompt import PromptStrategyType

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional engineer; the main goal is to write PEP8 compliant, elegant, modular, easy to read and maintain Python 3.9 code (but you can also use other programming language)
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

## Code: {filename} Write code with triple quotes, based on the following list and context.
1. Do your best to implement THIS ONLY ONE FILE. ONLY USE EXISTING API. IF NO API, IMPLEMENT IT.
2. Requirement: Based on the context, implement one following code file, note to return only in code form, your code will be part of the entire project, so please implement complete, reliable, reusable code snippets
3. Attention1: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
4. Attention2: YOU MUST FOLLOW "Data structures and interface definitions". DONT CHANGE ANY DESIGN.
5. Think before writing: What should be implemented and provided in this document?
6. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
7. Do not use public member functions that do not exist in your design.

-----
# Context
{context}
-----
## Format example
-----
## Code: {filename}
```python
## {filename}
...
```
-----
"""

COT_PROMPT_GENERATE_PLAN = """
-----
# Context
{context}
-----
NOTICE
Role: You are a professional engineer; Given the previous context, the main goal is to create a tutorial-like step by step plan for writing {filename} in Python 3.9 code (but you can also use other programming language)
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".
-----
## Step by Step Implementation Plan: {filename}
"""

COT_PROMPT_CODE_TEMPLATE = """
-----
# Context
{context}
-----
{plan}
-----
NOTICE
Role: You are a professional engineer; the main goal is to write PEP8 compliant, elegant, modular, easy to read and maintain Python 3.9 code (but you can also use other programming language)
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

## Code: {filename} Write code with triple quotes, based on the following constraints and context.
1. Do your best to implement THIS ONLY ONE FILE. ONLY USE EXISTING API. IF NO API, IMPLEMENT IT.
2. Requirement: Closely follow the step by step implementation plan above and implement one following code file, note to return only in code form, your code will be part of the entire project, so please implement complete, reliable, reusable code snippets
3. Attention1: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
4. Attention2: YOU MUST FOLLOW "Data structures and interface definitions". DONT CHANGE ANY DESIGN.
5. Think before writing: What should be implemented and provided in this document?
6. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
7. Do not use public member functions that do not exist in your design.
-----
## Format example
-----
## Code: {filename}
```python
## {filename}
...
```
-----
"""

#Tree of Thought will have depth 4+ for Engineer role
TOT_PROMPT_GENERATE_PLAN=""#Create a feasible plan for implementing the current file in tutorial style
TOT_PROMPT_WRITE_INTERFACE=""#From the tutorial style plan, generate the python interface of the class
TOT_PROMPT_IMPLEMENT_ONE_FUNCTION=""#Following the interface, implement one function at a time
TOT_PROMPT_EVALUATE_STEP=""#Evaluation prompt for checking if the current intermediate generated code is correct, if not backtrack

class WriteCode(Action):
    def __init__(self, name="WriteCode", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    def _is_invalid(self, filename):
        return any(i in filename for i in ["mp3", "wav"])

    def _save(self, context, filename, code):
        # logger.info(filename)
        # logger.info(code_rsp)
        if self._is_invalid(filename):
            return

        design = [i for i in context if i.cause_by == WriteDesign][0]

        ws_name = CodeParser.parse_str(block="Python package name", text=design.content)
        ws_path = WORKSPACE_ROOT / ws_name
        if f"{ws_name}/" not in filename and all(i not in filename for i in ["requirements.txt", ".md"]):
            ws_path = ws_path / ws_name
        code_path = ws_path / filename
        code_path.parent.mkdir(parents=True, exist_ok=True)
        code_path.write_text(code)
        logger.info(f"Saving Code to {code_path}")
    
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt: str, strategy: PromptStrategyType, task: Task = None):
        if strategy == PromptStrategyType.NAIVE:
            code_rsp = await self._aask(prompt)

        elif strategy == PromptStrategyType.CHAIN_OF_THOUGHT:
            task = Task(# each task consists of an ordered list of prompts
                        prompts = [COT_PROMPT_GENERATE_PLAN, COT_PROMPT_CODE_TEMPLATE],
                        # a pool of key value pairs to format the prompts
                        task_args_pool = {
                            "context": context, 
                            "filename": filename, 
                            # intermediate result is empty
                            "plan": ""
                        },
                        # an ordered list of prompt output keys
                        task_output_keys = ["plan", "code"])
            cot_solver = COT(prompt, self._aask, task = task)
            success, code_rsp = await cot_solver.solve()
        elif strategy == PromptStrategyType.TREE_OF_THOUGHT:
            task = Task(# each task consists of an ordered list of prompts
                        prompts = [TOT_PROMPT_GENERATE_PLAN, 
                                   TOT_PROMPT_WRITE_INTERFACE,
                                   TOT_PROMPT_IMPLEMENT_ONE_FUNCTION,
                                   TOT_PROMPT_EVALUATE_STEP,
                                   ],
                        # a pool of key value pairs to format the prompts
                        task_args_pool = {
                            #"context": context, 
                            #"filename": filename, 
                            # intermediate result is empty
                            #"plan": ""
                        },
                        # an ordered list of prompt output keys
                        #task_output_keys = ["plan", "code"]
                        )
            tot_solver = TOT(prompt, self._aask, task = task)
            success, code_rsp = await tot_solver.solve()
        else:
            logger.info(f'Strategy not implemented')
            raise NotImplementedError()
        code_rsp = await self._aask(prompt, strategy = strategy, task = task)
        logger.info(code_rsp)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code
    
    async def run(self, context, filename, strategy = CONFIG.prompt_strategy):
        strategy = PromptStrategyType(strategy)
        prompt = PROMPT_TEMPLATE.format(context=context, filename=filename)
        code = await self.write_code(prompt, strategy = strategy)

        logger.info(f'Writing {filename}..')
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        return code
    