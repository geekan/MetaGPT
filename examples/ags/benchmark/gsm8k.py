# -*- coding: utf-8 -*-
# @Date    :
# @Author  : all
# @Desc    : test on gsm8k

import re
import json
import asyncio
import aiofiles
import pandas as pd
from typing import Optional, List, Tuple, Callable
from tqdm.asyncio import tqdm_asyncio

from examples.ags.benchmark.utils import generate_random_indices

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


async def load_data(file_path: str, samples=1, test=False) -> List[dict]:
    data = []
    async with aiofiles.open(file_path, mode="r") as file:
        async for line in file:
            data.append(json.loads(line))
    random_indices = generate_random_indices(len(data), samples, test=test)
    data = [data[i] for i in random_indices]
    return data
        
def save_results_to_csv(results: List[Tuple[str, str, str, int, str]], path: str) -> Tuple[float, float]:
    """Save results to CSV file"""
    df = pd.DataFrame(results, columns=["question", "prediction", "expected_output", "score", "cost"])
    average_score = df["score"].mean()
    total_cost = df["cost"].iloc[-1]

    output_file = f"{path}/{average_score:.5f}.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")
    return average_score, total_cost

async def evaluate_problem(input: str, graph: Callable, expected_output: str) -> Tuple[str, str, str, int, str]:
    """Evaluate a single problem"""
    prompt = input
    max_retries = 5
    retries = 0
    prediction = await graph(prompt)
    cost = prediction[1]
    output = prediction[0]["solution"]

    print(output)

    score = loose_match_score(expected_output, output)
    # break
    # while retries < max_retries:
    #     try:
    #         prediction = await graph(prompt)
    #         cost = prediction[1]
    #         output = prediction[0]["solution"]

    #         score = loose_match_score(expected_output, output)
    #         break

    #     except Exception as e:
    #         retries += 1
    #         print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

    #         if retries == max_retries:
    #             print("Maximum retries reached. Skipping this sample.")
    #             output = None
    #             cost = None
    #             score = 0
    #             break

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

async def gsm8k_evaluation(graph: Callable, file_path: str, samples: int, path: str, test=False) -> Tuple[float, float]:
    """GSM8K evaluation main function"""
    data = await load_data(file_path, samples, test=test)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=5)
    average_score, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, total_cost
