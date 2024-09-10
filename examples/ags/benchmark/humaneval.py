import json
import asyncio
import aiofiles
import pandas as pd
from typing import List, Tuple, Callable
from tqdm.asyncio import tqdm_asyncio

from examples.ags.benchmark.utils import generate_random_indices

PASS = "pass"
FAIL = "fail"

async def load_data(file_path: str, samples=1) -> List[dict]:
    data = []
    async with aiofiles.open(file_path, mode="r") as file:
        async for line in file:
            data.append(json.loads(line))
    random_indices = generate_random_indices(len(data), samples)
    data = [data[i] for i in random_indices]
    return data

async def check_solution(solution, test_cases, entry_point):
    # Define a local dictionary to execute the solution
    local_dict = {}
    exec("from typing import List\n\n" + solution, {}, local_dict)

    # Ensure the entry point function is defined
    if entry_point not in local_dict:
        raise ValueError(f"Function {entry_point} is not defined in the solution.")

    details = [False for _ in range(len(test_cases))]

    # Check each test case
    for i, test in enumerate(test_cases):
        # Replace 'candidate' with the actual function call
        test_expr = test.replace("candidate", entry_point)
        try:
            # Evaluate the test case
            if eval(test_expr, {}, local_dict):
                details[i] = True
        except Exception as e:
            print(f"Error evaluating test case '{test}': {e}")

    if all(details):
        return PASS, details

    return FAIL, details

async def evaluate_problem(data: dict, graph: Callable) -> Tuple[str, str, str, int]:
    max_retries = 5
    retries = 0

    while retries < max_retries:
        try:
            solution = await graph(data["prompt"]) if graph else "None"
            ret = await check_solution(solution, data["test_cases"], data["entry_point"])

            score = 1 if ret[0] == PASS else 0
            break

        except Exception as e:
            retries += 1
            print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

            if retries == max_retries:
                print("Maximum retries reached. Skipping this sample.")
                solution = None
                ret = (FAIL, [])
                score = 0
                break

    return data["prompt"], solution, ret[1], score

async def evaluate_all_problems(data: List[dict], graph: Callable, max_concurrent_tasks: int = 50) -> List[Tuple[str, str, str, int]]:
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            return await evaluate_problem(problem, graph)

    tasks = [sem_evaluate(problem) for problem in data]

    return await tqdm_asyncio.gather(*tasks, desc="Evaluating HumanEval problems", total=len(data))

import os
import time
import json

def save_results_to_jsonl(results: List[Tuple[str, str, str, int]], path: str) -> float:
    avg_score = 0
    timestamp = int(time.time())
    filename = f"humaneval_results_{timestamp}.jsonl"
    full_path = os.path.join(path, filename)

    with open(full_path, "w") as f:
        for result in results:
            f.write(
                json.dumps(
                    {
                        "question": result[0],
                        "prediction": result[1],
                        "test_case_details": result[2],
                        "score": result[3],
                    }
                )
                + "\n"
            )
            avg_score += result[3]
    print(f"save to {full_path}")
    avg_score /= len(results)

    return round(avg_score, 5)

async def humaneval_evaluation(graph: Callable, file_path: str, samples: int, path: str) -> float:
    data = await load_data(file_path, samples)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=20)
    average_score = save_results_to_jsonl(results, path=path)
    print(f"Average score on HumanEval dataset: {average_score:.5f}")
    return average_score
