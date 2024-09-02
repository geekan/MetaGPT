# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 10:00 AM
# @Author  : all
# @Desc    : evaluate for different dataset
import asyncio
import json
import re
from typing import List, Literal, Optional, Tuple

import aiofiles
import pandas as pd
from tqdm.asyncio import tqdm_asyncio

# TODO 完成实验数据集的手动划分

DatasetType = Literal["HumanEval", "MMBP", "Gsm8K", "MATH", "HotpotQa", "MMLU"]


class Evaluator:
    """
    在这里完成对不同数据集的评估
    """

    def __init__(self, eval_path: str):
        self.eval_path = eval_path

    def validation_evaluate(self, dataset: DatasetType, graph, params: dict, path):
        """
        Evaluates on validation dataset.
        """
        if dataset == "Gsm8K":
            score = self._gsm8k_eval(graph, params, path)
            return score
        pass

    def test_evaluate(self, dataset: DatasetType):
        """
        Evaluates on test dataset.
        """
        pass

    async def _gsm8k_eval(self, graph_class, params, path, samples: int = 10):
        """
        Evaluate on GSM8K dataset.
        """

        # 模拟加载模型的函数
        async def load_graph():
            dataset = params["dataset"]
            llm_config = params["llm_config"]
            graph = graph_class(name="Gsm8K", llm_config=llm_config, dataset=dataset)
            return graph

        # 清理文本并提取单个数字
        def extract_number(text: str) -> Optional[float]:
            # 使用正则表达式提取数字，包括整数和浮点数
            matches = re.findall(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?|\d+\.\d+", text)
            print(matches)
            if matches:
                # 获取最后一个匹配的数字
                last_number = matches[-1]

                # 移除逗号以统一格式
                last_number = last_number.replace(",", "")

                try:
                    return float(last_number)
                except ValueError:
                    return None
            else:
                return None

        # 宽松匹配分数计算函数
        def loose_match_score(expected_output: str, prediction: str, tolerance: float = 1e-6) -> int:
            expected_number = extract_number(expected_output)
            predicted_number = extract_number(prediction)

            print(predicted_number)

            # 如果预期输出或预测输出为空，返回不匹配
            if expected_number is None or predicted_number is None:
                return 0

            # 比较两个提取出的数字，允许一定的容差
            if abs(expected_number - predicted_number) <= tolerance:
                return 1  # 数字相近，认为匹配成功
            else:
                return 0  # 数字不匹配

        # 异步评估单个问题
        async def _evaluate_problem(input: str, graph, expected_output: str) -> Tuple[str, str, str, int]:
            prompt = input

            print("Question", prompt)
            max_retries = 5
            retries = 0

            while retries < max_retries:
                try:
                    # 假设模型有一个异步生成函数
                    prediction = await graph(prompt) if graph else "None"  # 这是一个占位符，替换成实际的模型生成逻辑
                    print(type(prediction))
                    print("预测", prediction[0])

                    score = loose_match_score(expected_output, prediction[0]["response"])
                    break

                except Exception as e:
                    retries += 1
                    print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                    if retries == max_retries:
                        print("Maximum retries reached. Skipping this sample.")
                        prediction = None
                        score = 0
                        break

            return input, prediction, expected_output, score

        # 异步读取JSONL文件
        async def load_data(file_path: str) -> List[dict]:
            data = []
            async with aiofiles.open(file_path, mode="r") as file:
                async for line in file:
                    data.append(json.loads(line))
            return data[:samples]

        # 并行评估所有问题
        async def evaluate_all_problems(data: List[dict], graph, max_concurrent_tasks: int = 1):
            semaphore = asyncio.Semaphore(max_concurrent_tasks)

            async def sem_evaluate(problem):
                async with semaphore:
                    input_text = problem["question"]
                    expected_output = problem["answer"]
                    return await _evaluate_problem(input_text, graph, expected_output)

            tasks = [sem_evaluate(problem) for problem in data]

            # 使用tqdm.gather来显示进度条
            return await tqdm_asyncio.gather(*tasks, desc="Evaluating problems", total=len(data))

        # 保存结果到CSV文件
        def save_results_to_csv(results: List[Tuple[str, str, str, int]], path):
            df = pd.DataFrame(results, columns=["question", "prediction", "expected_output", "score"])
            average_score = df["score"].mean()

            # 生成文件名，保留五位小数
            output_file = f"{path}/{average_score:.5f}.csv"
            df.to_csv(output_file, index=False)
            print(f"Results saved to {output_file}")

            return average_score

        async def gsm8k():
            file_path = "examples/ags/data/gsm8k.jsonl"  # 替换为您的JSONL文件路径
            data = await load_data(file_path)

            graph = await load_graph()

            # TODO 这里需要查看Graph的结构为什么没有办法实现
            print("--------------")
            print(graph)
            print("--------------")
            results = await evaluate_all_problems(data, graph, max_concurrent_tasks=20)

            # 保存结果到CSV文件并获取平均分
            average_score = save_results_to_csv(results, path=path)

            print(f"Average score: {average_score:.5f}")
            return average_score

        score = await gsm8k()

        return score


if __name__ == "__main__":

    def extract_number(text: str) -> Optional[float]:
        # 使用正则表达式提取数字，包括整数和浮点数
        matches = re.findall(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.\d+", text)
        print(matches)
        if matches:
            # 获取最后一个匹配的数字
            last_number = matches[-1]

            # 移除逗号以统一格式
            last_number = last_number.replace(",", "")

            try:
                return float(last_number)
            except ValueError:
                return None
        else:
            return None

    num = extract_number(
        r"To determine how much Janet makes every day at the farmers' market, we need to follow these steps:\n\n1. **Calculate the total number of eggs Janet uses daily:**\n   - She eats 3 eggs for breakfast.\n   - She uses 4 eggs to bake muffins.\n   - Total eggs used = 3 (for breakfast) + 4 (for muffins) = 7 eggs.\n\n2. **Determine the number of eggs left to sell:**\n   - Total eggs laid per day = 16 eggs.\n   - Eggs left after use = 16 (total eggs) - 7 (eggs used) = 9 eggs.\n\n3. **Calculate the revenue from selling the remaining eggs:**\n   - She sells each egg for $2.\n   - Total revenue = 9 (eggs left) * $2 (price per egg) = $18.\n\nThus, Janet makes $18,000 every day at the farmers' market."
    )
    print(num)
