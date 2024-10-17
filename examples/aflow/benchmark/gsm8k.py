# -*- coding: utf-8 -*-
# @Date    :
# @Author  : all
# @Desc    : test on gsm8k
import re
import json
import asyncio
import aiofiles
import pandas as pd
from typing import Optional, List, Tuple, Callable, Any

from pandas import Series
from tqdm.asyncio import tqdm_asyncio
import os
import time
from datetime import datetime


def extract_number(text: str) -> Optional[float]:
    """Clean text and extract a single number"""
    matches = re.findall(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?|\d+\.\d+", str(text))
    if matches:
        last_number = matches[-1].replace(",", "")
        try:
            return float(last_number)
        except ValueError:
            return None
    else:
        return None


def loose_match_score(expected_output: float, prediction: float, tolerance: float = 1e-6) -> int:
    # 如果预测输出为空，返回不匹配
    if prediction is None:
        return 0

    a = expected_output
    b = prediction

    # 比较两个提取出的数字，允许一定的容差
    if abs(a - b) <= tolerance:
        return 1  # 数字相近，认为匹配成功
    else:
        return 0  # 数字不匹配


def log_mismatch(problem: str, expected_output: float, prediction: str, predicted_number: float, path):
    log_data = {
        "question": problem,
        "right_answer": expected_output,
        "model_output": prediction,
        "extracted_output": predicted_number
    }

    log_file = os.path.join(path, 'log.json')

    # 检查log文件是否已经存在
    if os.path.exists(log_file):
        # 如果存在，加载现有的日志数据
        with open(log_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        # 如果不存在，创建一个新的日志列表
        data = []

    # 添加新的日志记录
    data.append(log_data)

    # 将数据写回到log.json文件
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


async def load_data(file_path: str, specific_indices: List[int] = None) -> List[dict]:
    data = []
    # 异步读取文件内容
    async with aiofiles.open(file_path, mode="r", encoding='utf-8') as file:
        async for line in file:
            data.append(json.loads(line))

    # 然后在随机选择的样本中基于特定索引列表进行进一步筛选
    if specific_indices is not None:
        filtered_data = [data[i] for i in specific_indices if i < len(data)]
        return filtered_data

    return data


def save_results_to_csv(results: List[Tuple[str, str, str, int]], path):
    # 创建 DataFrame
    df = pd.DataFrame(results, columns=["question", "prediction", "expected_output", "score", "cost"])

    # 计算统计数据
    avg_score = df["score"].mean()
    t_cost = df["cost"].max()
    a_cost = t_cost / len(df) if len(df) > 0 else 0

    # 获取当前时间，格式为 YYYYMMDD_HHMMSS
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 生成文件名，包含平均分和当前时间，保留五位小数
    filename = f"{avg_score:.5f}_{current_time}.csv"
    output_file = os.path.join(path, filename)

    # 保存到 CSV
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

    return avg_score, a_cost, t_cost


async def evaluate_problem(input: str, graph, expected_output: str, path) -> tuple[
    str, str , float, int, str]:
    max_retries = 5
    retries = 0
    uni_score = 0

    while retries < max_retries:
        try:
            prediction = await graph(input) if graph else "None"  # 这是一个占位符，替换成实际的模型生成逻辑
            cost = prediction[1]
            output = prediction[0]
            if output is not None:
                predicted_number = extract_number(output)
                expected_output = extract_number(expected_output)
            else:
                predicted_number = None

            uni_score = loose_match_score(expected_output, predicted_number)

            if uni_score == 0:
                log_mismatch(input, expected_output, output, predicted_number, path)
            else:
                pass

            break

        except Exception as e:
            retries += 1
            print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")
            time.sleep(5 * retries)

            if retries == max_retries:
                print("Maximum retries reached. Skipping this sample.")
                output = e
                cost = None
                uni_score = 0
                break

    return input, output, expected_output, uni_score, cost


async def evaluate_all_problems(data: List[dict], graph, path, max_concurrent_tasks: int = 100):
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            input_text = problem["question"]
            expected_output = problem["answer"]
            return await evaluate_problem(input_text, graph, expected_output, path)

    tasks = [sem_evaluate(problem) for problem in data]

    # 使用tqdm.gather来显示进度条
    return await tqdm_asyncio.gather(*tasks, desc="Evaluating problems", total=len(data))

async def optimize_gsm8k_evaluation(graph: Callable, file_path: str, path: str, va_list: list) -> tuple[
    Any, Any, Any]:
    """Optimize GSM8K evaluation main function"""
    data = await load_data(file_path, va_list)
    results = await evaluate_all_problems(data, graph, path, max_concurrent_tasks=30)
    average_score, average_cost, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, average_cost, total_cost
