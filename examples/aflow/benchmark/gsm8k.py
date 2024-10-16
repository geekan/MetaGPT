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
import os
import time
from datetime import datetime

from examples.aflow.benchmark.utils import generate_random_indices, log_mismatch

def extract_number(text: str) -> Optional[float]:
    """Clean text and extract a single number"""
    print(f"text: {text}")
    matches = re.findall(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?|\d+\.\d+", str(text))
    print(f"matches: {matches}")
    if matches:
        last_number = matches[-1].replace(",", "")
        try:
            return float(last_number)
        except ValueError:
            return None
    else:
        return None

def loose_match_score(expected_output: float, prediction: float, tolerance: float = 1e-6) -> int:
    if prediction is None:
        return 0
    
    if abs(expected_output - prediction) <= tolerance:
        return 1
    else:
        return 0
        
def save_results_to_csv(results: List[Tuple[str, str, str, int, str]], path: str) -> Tuple[float, float, float]:
    df = pd.DataFrame(results, columns=["question", "prediction", "expected_output", "score", "cost"])
    avg_score = df["score"].mean()
    t_cost = df["cost"].max()
    a_cost = t_cost / len(df) if len(df) > 0 else 0

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{avg_score:.5f}_{current_time}.csv"
    output_file = os.path.join(path, filename)

    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")
    return avg_score, a_cost, t_cost

async def evaluate_problem(input: str, graph: Callable, expected_output: str, path: str = None) -> Tuple[str, str, str, int, str]:
    max_retries = 10
    retries = 0
    uni_score = 0

    while retries < max_retries:
        try:
            prediction = await graph(input) if graph else None
            cost = prediction[1]
            output = prediction[0]

            if output is not None:
                predicted_number = extract_number(output)
                expected_number = extract_number(expected_output)
            else:
                predicted_number = None
                expected_number = extract_number(expected_output)

            print(f"predicted_number: {predicted_number}, expected_number: {expected_number}")
            uni_score = loose_match_score(expected_number, predicted_number)

            if uni_score == 0 and path is not None:
                log_mismatch(input, expected_output, output, predicted_number, path)

            break
    
        except Exception as e:
            retries += 1
            print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")
            time.sleep(5 * retries)

            if retries == max_retries:
                print("Maximum retries reached. Skipping this sample.")
                output = str(e)
                cost = None
                uni_score = 0
                break

    return input, output, expected_output, uni_score, cost

async def evaluate_all_problems(data: List[dict], graph: Callable, path, max_concurrent_tasks: int = 20) -> List[Tuple[str, str, str, int, str]]:
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            input_text = problem["question"]
            expected_output = problem["answer"]
            return await evaluate_problem(input_text, graph, expected_output, path)

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
    async with aiofiles.open(file_path, mode="r", encoding='utf-8') as file:
        async for line in file:
            data.append(json.loads(line))

    if specific_indices is not None:
        filtered_data = [data[i] for i in specific_indices if i < len(data)]
        return filtered_data

    return data

async def gsm8k_evaluation(graph: Callable, file_path: str, samples: int, path: str, test=False) -> Tuple[float, float]:
    data = await load_data(file_path, samples, test=test)
    results = await evaluate_all_problems(data, graph, path, max_concurrent_tasks=20)
    average_score, average_cost, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, total_cost

async def optimize_gsm8k_evaluation(graph: Callable, file_path: str, path: str, va_list: list) -> Tuple[Any, Any, Any]:
    data = await load_file_data(file_path, va_list)
    results = await evaluate_all_problems(data, graph, path, max_concurrent_tasks=8)
    average_score, average_cost, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, average_cost, total_cost