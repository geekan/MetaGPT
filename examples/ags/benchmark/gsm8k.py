# -*- coding: utf-8 -*-
# @Date    :
# @Author  : issac
# @Desc    : test on gsm8k

import datetime
import os
import json
import subprocess
import sys
import asyncio
import aiofiles
from metagpt.llm import LLM
from examples.ags.w_action_node.graph import Gsm8kGraph
from examples.ags.w_action_node.operator import GenerateCode, GenerateCodeBlock
from deepeval.benchmarks import GSM8K
from deepeval.benchmarks.gsm8k.template import GSM8KTemplate
import pandas as pd

solver = Gsm8kGraph(name="solver", llm=LLM())

from deepeval.models.base_model import DeepEvalBaseLLM


# 这里是DeepEval强制定义的模型基础格式，这里不需要进行改动，只需要调用即可
class OpenAI(DeepEvalBaseLLM):
    def __init__(self):
        self.solver = Gsm8kGraph(name="solver", llm=LLM())

    def load_model(self):
        # 这里应该是加载模型的逻辑
        pass

    async def a_generate(self, prompt: str) -> str:
        solution_result = await self.solver(prompt)
        return solution_result['solution']

    def generate(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        solution_result = loop.run_until_complete(self.a_generate(prompt))  # 等待 a_generate 方法完成
        return solution_result

    def get_model_name(self):
        return "Custom Azure OpenAI Model"

async def async_evaluate_problem(model, golden, benchmark):
    prompt = GSM8KTemplate.generate_output(
        train_set=benchmark.shots_dataset,
        input=golden.input,
        n_shots=benchmark.n_shots,
        enable_cot=benchmark.enable_cot,
    )
    prediction = await model.a_generate(prompt)
    score = benchmark.scorer.exact_match_score(golden.expected_output, prediction)
    return golden.input, prediction, golden.expected_output, score


async def evaluate_benchmark(benchmark, model):
    goldens = benchmark.load_benchmark_dataset()[:benchmark.n_problems]
    tasks = [async_evaluate_problem(model, golden, benchmark) for golden in goldens]
    results = await asyncio.gather(*tasks)

    overall_correct_predictions = sum(score for _, _, _, score in results)
    overall_total_predictions = benchmark.n_problems
    overall_accuracy = overall_correct_predictions / overall_total_predictions

    predictions_row = [(input, prediction, expected_output, score) for input, prediction, expected_output, score in
                       results]
    benchmark.predictions = pd.DataFrame(predictions_row,
                                         columns=["Input", "Prediction", "Expected Output", "Correct"])
    benchmark.overall_score = overall_accuracy

    now = datetime.datetime.now().time()
    now_time = now.strftime("%Y-%m-%d_%H-%M-%S").replace(':', '_')

    # Save the detailed data to a CSV file
    benchmark.predictions.to_csv(f'gsm8k_{overall_accuracy}_{now_time}.csv', index=False)

    print(f"Overall GSM8K Accuracy: {overall_accuracy}")
    return overall_accuracy

if __name__ == '__main__':

    # 申明模型
    openai = OpenAI()

    # 定义 benchmark,problems代表测试问题数,注释掉就可以完整测试,n_shot设置为0当前为zero shot,enable_cot是官方的COT的Prompt，建议关闭，用我们自己的graph实现
    benchmark = GSM8K(
        n_problems=10,
        n_shots=0,
        enable_cot=False
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(evaluate_benchmark(benchmark, openai))

    # Print the overall score
    print(benchmark.overall_score)
