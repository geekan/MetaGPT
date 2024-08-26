# -*- coding: utf-8 -*-
# @Date    : 8/23/2024 10:00 AM
# @Author  : all
# @Desc    : evaluate for different dataset
import datetime
import inspect
import os
from typing import Literal

import pandas as pd
from deepeval.benchmarks import GSM8K

from examples.ags.benchmark.gsm8k import GraphModel
from examples.ags.w_action_node.graph import SolveGraph

# TODO 完成实验数据集的手动划分

DatasetType = Literal["HumanEval", "MMBP", "Gsm8K", "MATH", "HotpotQa", "MMLU"]


class Evaluator:
    """
    在这里完成对不同数据集的评估
    """

    def __init__(self, eval_path: str):
        self.eval_path = eval_path

    def validation_evaluate(self, dataset: DatasetType, graph, params: dict):
        """
        Evaluates on validation dataset.
        """
        if dataset == "Gsm8K":
            return self._gsm8k_eval(graph, params)
        pass

    def test_evaluate(self, dataset: DatasetType):
        """
        Evaluates on test dataset.
        """
        pass

    def _gsm8k_eval(self, graph_class, params, samples: int = 1000):
        """
        Evaluate on GSM8K dataset.
        """

        # TODO 划分验证集测试集
        def _evaluate_problem(model, golden, benchmark):
            prompt = golden.input

            max_retries = 50
            retries = 0

            while retries < max_retries:
                try:
                    prediction = model.a_generate(prompt)
                    score = benchmark.scorer.exact_match_score(golden.expected_output, prediction)
                    break

                except Exception as e:
                    retries += 1
                    print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

                    if retries == max_retries:
                        print("Maximum retries reached. Skipping this sample.")
                        prediction = None
                        score = 0
                        break

            return golden.input, str(prediction), golden.expected_output, score

        def process_gsm8k_csv(file_path, tolerance=1e-6):
            # 读取 CSV 文件
            df = pd.read_csv(file_path, dtype=str)  # 使用默认逗号分隔符，并指定所有列为字符串类型

            # 清理预测和期望输出列
            df["prediction"] = df["prediction"].str.strip()
            df["prediction"] = df["prediction"].str.replace(",", "", regex=True)
            df["expected output"] = df["expected output"].str.strip()
            df["expected output"] = df["expected output"].str.replace(",", "", regex=True)

            # 将列转换为数值类型
            df["prediction"] = pd.to_numeric(df["prediction"], errors="coerce")
            df["expected output"] = pd.to_numeric(df["expected output"], errors="coerce")

            # 计算 score 列
            # 对于浮点数，使用近似相等的逻辑
            df["score"] = (df["prediction"] - df["expected output"]).abs() <= tolerance

            # 将布尔值转换为整数
            df["score"] = df["score"].astype(int)

            # 计算 score 列的平均值
            average_score = df["score"].mean()

            # 获取输入文件的目录
            input_dir = os.path.dirname(file_path)

            # 创建输出文件路径
            output_file_name = f"{average_score:.4f}.csv"
            output_file_path = os.path.join(input_dir, output_file_name)

            # 写入新的 CSV 文件
            df.to_csv(output_file_path, index=False)

            print(f"Data written to {output_file_path}")
            print(f"Average score: {average_score:.4f}")

            # 统计空值数量
            num_empty_predictions = df["prediction"].isna().sum()

            # 删除包含空 prediction 的行
            df = df.dropna(subset=["prediction"])

            # 重新计算正确的、错误的以及空的个数
            num_correct = (df["score"] == 1).sum()
            num_incorrect = (df["score"] == 0).sum()

            print(f"Number of empty predictions: {num_empty_predictions}")
            print(f"Number of correct predictions after removing empty ones: {num_correct}")
            print(f"Number of incorrect predictions after removing empty ones: {num_incorrect}")

            return average_score

        dataset = params["dataset"]
        llm_config = params["llm_config"]

        # TODO 给到的是load出来的Graph，怎么让他做实例化？
        graph = SolveGraph(name="Gsm8K", llm_config=llm_config, dataset=dataset)
        model = GraphModel(graph)
        benchmark = GSM8K(n_problems=samples, n_shots=0, enable_cot=False)

        graph_module = inspect.getmodule(graph_class)
        os.path.dirname(graph_module.__file__)
        goldens = benchmark.load_benchmark_dataset()[: benchmark.n_problems]

        results = [_evaluate_problem(model, golden, benchmark) for golden in goldens]

        overall_correct_predictions = sum(score for _, _, _, score in results)
        overall_total_predictions = benchmark.n_problems
        overall_accuracy = overall_correct_predictions / overall_total_predictions

        predictions_row = [
            (input, prediction, expected_output, score) for input, prediction, expected_output, score in results
        ]
        benchmark.predictions = pd.DataFrame(
            predictions_row, columns=["input", "prediction", "expected output", "score"]
        )
        benchmark.overall_score = overall_accuracy
        now = datetime.datetime.now()
        now_time = now.strftime("%Y-%m-%d_%H-%M-%S").replace(":", "_")

        file_path = f"{self.eval_path}/gsm8k_{overall_accuracy}_{now_time}.csv"

        benchmark.predictions.to_csv(file_path, index=False)

        score = process_gsm8k_csv(file_path=file_path)
        return {"score": score}
