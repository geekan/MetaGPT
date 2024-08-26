# -*- coding: utf-8 -*-
# @Date    :
# @Author  : issac
# @Desc    : test on gsm8k
import asyncio

from deepeval.models.base_model import DeepEvalBaseLLM


# 这里是DeepEval强制定义的模型基础格式，这里不需要进行改动，只需要调用即可
class GraphModel(DeepEvalBaseLLM):
    def __init__(self, graph):
        self.solver = graph

    def load_model(self):
        pass

    async def a_generate(self, prompt: str) -> str:
        # TODO 还需要在这里继续整合Cost
        solution_result, total_cost = await self.solver(prompt)
        return solution_result

    def generate(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        solution_result = loop.run_until_complete(self.a_generate(prompt))  # 等待 a_generate 方法完成
        return solution_result

    def get_model_name(self):
        return "Custom Azure OpenAI Model"
