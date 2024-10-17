# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 17:36 PM
# @Author  : didi
# @Desc    : operator demo of ags
import concurrent
import sys
import traceback
from typing import List

from tenacity import retry, stop_after_attempt, wait_fixed

from examples.aflow.scripts.optimized.GSM8K.workflows.template.operator_an import *
from examples.aflow.scripts.optimized.GSM8K.workflows.template.op_prompt import *
from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM
import asyncio
import logging

class Operator:
    def __init__(self, name, llm: LLM):
        self.name = name
        self.llm = llm

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class Custom(Operator):
    def __init__(self, llm: LLM, name: str = "Custom"):
        super().__init__(name, llm)

    async def __call__(self, input, instruction):
        prompt = instruction + input
        node = await ActionNode.from_pydantic(GenerateOp).fill(context=prompt, llm=self.llm, mode="single_fill")
        response = node.instruct_content.model_dump()
        return response


def run_code(code):
    try:
        # 创建一个新的全局命名空间
        global_namespace = {}

        disallowed_imports = [
            "os", "sys", "subprocess", "multiprocessing",
            "matplotlib", "seaborn", "plotly", "bokeh", "ggplot",
            "pylab", "tkinter", "PyQt5", "wx", "pyglet"
        ]

        # 检查禁止导入的库
        for lib in disallowed_imports:
            if f"import {lib}" in code or f"from {lib}" in code:
                logging.warning("检测到禁止导入的库: %s", lib)
                return "Error", f"禁止导入的库: {lib} 以及绘图类功能"

        # 使用 exec 执行代码
        exec(code, global_namespace)
        # 假设代码中定义了一个名为 'solve' 的函数
        if 'solve' in global_namespace and callable(global_namespace['solve']):
            result = global_namespace['solve']()
            return "Success", str(result)
        else:
            return "Error", "未找到 'solve' 函数"
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_str = traceback.format_exception(exc_type, exc_value, exc_traceback)
        return "Error", f"执行错误: {str(e)}\n{''.join(tb_str)}"
    

class Programmer(Operator):
    def __init__(self, llm: LLM, name: str = "Programmer"):
        super().__init__(name, llm)

    async def exec_code(self, code, timeout=30):
        """
        异步执行代码，并在超时时返回错误。
        """
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
            try:
                # 提交 run_code 任务到进程池
                future = loop.run_in_executor(executor, run_code, code)
                # 等待任务完成或超时
                result = await asyncio.wait_for(future, timeout=timeout)
                return result
            except asyncio.TimeoutError:
                # 超时，尝试关闭进程池
                executor.shutdown(wait=False, cancel_futures=True)
                return "Error", "代码执行超时"
            except Exception as e:
                return "Error", f"未知错误: {str(e)}"

    async def code_generate(self, problem, analysis, feedback, mode):
        """
        生成代码的异步方法。
        """
        prompt = PYTHON_CODE_VERIFIER_PROMPT.format(
            problem=problem,
            analysis=analysis,
            feedback=feedback
        )
        fill_kwargs = {
            "context": prompt,
            "llm": self.llm,
            "function_name": "solve"
        }
        if mode:
            fill_kwargs["mode"] = mode
        node = await ActionNode.from_pydantic(CodeGenerateOp).fill(**fill_kwargs)
        response = node.instruct_content.model_dump()
        return response

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def __call__(self, problem: str, analysis: str = "None"):
        """
        调用方法，生成代码并执行，最多重试 3 次。
        """
        code = None
        output = None
        feedback = ""
        for i in range(3):
            code_response = await self.code_generate(problem, analysis, feedback, mode="code_fill")
            code = code_response.get("code")
            if not code:
                return {"code": code, "output": "未生成代码"}
            status, output = await self.exec_code(code)
            if status == "Success":
                return {"code": code, "output": output}
            else:
                print(f"第{i + 1}次执行错误，错误信息：{output}")
                feedback = (
                    f"\nThe result of the error from the code you wrote in the previous round:\n"
                    f"Code: {code}\n\nStatus: {status}, {output}"
                )
        return {"code": code, "output": output}


class ScEnsemble(Operator):
    """
    Paper: Self-Consistency Improves Chain of Thought Reasoning in Language Models
    Link: https://arxiv.org/abs/2203.11171
    Paper: Universal Self-Consistency for Large Language Model Generation
    Link: https://arxiv.org/abs/2311.17311
    """

    def __init__(self,llm: LLM , name: str = "ScEnsemble"):
        super().__init__(name, llm)

    async def __call__(self, solutions: List[str], problem: str):
        answer_mapping = {}
        solution_text = ""
        for index, solution in enumerate(solutions):
            answer_mapping[chr(65 + index)] = index
            solution_text += f"{chr(65 + index)}: \n{str(solution)}\n\n\n"

        prompt = SC_ENSEMBLE_PROMPT.format(solutions=solution_text, problem=problem)
        node = await ActionNode.from_pydantic(ScEnsembleOp).fill(context=prompt, llm=self.llm)
        response = node.instruct_content.model_dump()

        answer = response.get("solution_letter", "")
        answer = answer.strip().upper()

        return {"response": solutions[answer_mapping[answer]]}