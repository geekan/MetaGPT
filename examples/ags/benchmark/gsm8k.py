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
from tqdm.asyncio import tqdm_asyncio

from examples.ags.benchmark.utils import generate_random_indices, log_mismatch

def extract_number(text: str) -> Optional[float]:
    """Clean text and extract a single number"""
    matches = re.findall(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?|\d+\.\d+", text)
    if matches:
        last_number = matches[-1].replace(",", "")
        try:
            return float(last_number)
        except ValueError:
            return None
    else:
        return None

def loose_match_score(expected_output: str, prediction: str, tolerance: float = 1e-6) -> int:
    """Loose match score calculation function"""
    expected_number = extract_number(expected_output)
    predicted_number = extract_number(prediction)

    if expected_number is None or predicted_number is None:
        return 0

    if abs(expected_number - predicted_number) <= tolerance:
        return 1
    else:
        return 0
        
def save_results_to_csv(results: List[Tuple[str, str, str, int, str]], path: str) -> Tuple[float, float]:
    """Save results to CSV file"""
    df = pd.DataFrame(results, columns=["question", "prediction", "expected_output", "score", "cost"])
    average_score = df["score"].mean()
    total_cost = df["cost"].max()
    average_cost = total_cost / len(df) if len(df) > 0 else 0

    output_file = f"{path}/{average_score:.5f}.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")
    return average_score, average_cost, total_cost

async def evaluate_problem(input: str, graph: Callable, expected_output: str, path: str = None) -> Tuple[str, str, str, int, str]:
    """Evaluate a single problem"""
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            prediction = await graph(input) if graph else None
            cost = prediction[1]
            output = prediction[0]
            
            if output is not None:
                predicted_number = extract_number(output)
                expected_output = extract_number(expected_output)
            else:
                predicted_number = None

            uni_score = loose_match_score(expected_output, predicted_number)

            if uni_score == 0 and path is not None:
                log_mismatch(input, expected_output, output, predicted_number, path)
            else:
                pass

            break
    
        except Exception as e:
            retries += 1
            print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

            if retries == max_retries:
                print("Maximum retries reached. Skipping this sample.")
                output = str(e)
                cost = None
                score = 0
                break

    return input, output, expected_output, score, cost

async def evaluate_all_problems(data: List[dict], graph: Callable, max_concurrent_tasks: int = 20) -> List[Tuple[str, str, str, int, str]]:
    """Evaluate all problems"""
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            input_text = problem["question"]
            expected_output = problem["answer"]
            return await evaluate_problem(input_text, graph, expected_output)

    tasks = [sem_evaluate(problem) for problem in data]

    return await tqdm_asyncio.gather(*tasks, desc="Evaluating problems", total=len(data))

async def load_data(file_path: str, samples=1, test=False) -> List[dict]:
    data = []
    async with aiofiles.open(file_path, mode="r") as file:
        async for line in file:
            data.append(json.loads(line))
    random_indices = generate_random_indices(len(data), samples, test=test)
    data = [data[i] for i in random_indices]
    return data

async def load_file_data(file_path: str, specific_indices: List[int] = None) -> List[dict]:
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

async def gsm8k_evaluation(graph: Callable, file_path: str, samples: int, path: str, test=False) -> Tuple[float, float]:
    """GSM8K evaluation main function"""
    data = await load_data(file_path, samples, test=test)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=10)
    average_score, average_cost, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, total_cost

async def optimize_gsm8k_evaluation(graph: Callable, file_path: str, path: str, va_list: list) -> Tuple[Any, Any, Any]:
    """Optimize GSM8K evaluation main function"""
    data = await load_file_data(file_path, va_list)
    results = await evaluate_all_problems(data, graph, path, max_concurrent_tasks=50)
    average_score, average_cost, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, average_cost, total_cost

# TODO Benchmark 与 Evaluator 中主要修改四个地方
# 1. Evaluator.py 之中添加 val list
# 2. load_data 函数修改
# 3. result_to_csv 函数需要给 avg return
# 4. evaluate_problem 中添加log.json