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

async def check_solution(solution, test_cases, timeout=1):
    # Define a local dictionary to execute the solution
    local_dict = {}
    exec(solution, {}, local_dict)

    details = [False for _ in range(len(test_cases))]

    async def evaluate_test(test):
        # Delete 'assert' from test
        test_expr = test.replace("assert ", "")
        try:
            # Evaluate the test case with timeout
            await asyncio.wait_for(asyncio.to_thread(eval, test_expr, {}, local_dict), timeout)
            return True
        except asyncio.TimeoutError:
            print(f"Test case '{test}' timed out.")
        except Exception as e:
            print(f"Error evaluating test case '{test}': {e}")
        return False

    # Check each test case
    for i, test in enumerate(test_cases):
        result = await evaluate_test(test)
        details[i] = result
        if not result:
            return FAIL, details

    if all(details):
        return PASS, details

    return FAIL, details

async def evaluate_problem(data: dict, graph: Callable) -> Tuple[str, str, str, int]:
    max_retries = 5
    retries = 0

    while retries < max_retries:
        try:
            solution = await graph(data["prompt"]) if graph else "None"
            ret = await check_solution(solution, data["test_list"])

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

    return await tqdm_asyncio.gather(*tasks, desc="Evaluating MBPP problems", total=len(data))

def save_results_to_csv(results: List[Tuple[str, str, str, int]], path: str) -> float:
    df = pd.DataFrame(results, columns=["question", "prediction", "test_case_details", "score"])
    average_score = df["score"].mean()

    output_file = f"{path}/{average_score:.5f}.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

    return average_score

async def mbpp_evaluation(graph: Callable, file_path: str, samples: int, path: str) -> float:
    data = await load_data(file_path, samples)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=20)
    average_score = save_results_to_csv(results, path=path)
    print(f"Average score on MBPP dataset: {average_score:.5f}")
    return average_score
