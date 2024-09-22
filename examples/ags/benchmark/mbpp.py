import json
import time
import asyncio
import aiofiles
import pandas as pd
from typing import List, Tuple, Callable, Any, Optional, Dict
from tqdm.asyncio import tqdm_asyncio

from examples.ags.benchmark.utils import generate_random_indices

PASS = "pass"
FAIL = "fail"

async def load_data(file_path: str, samples=1, test=False) -> List[dict]:
    data = []
    async with aiofiles.open(file_path, mode="r") as file:
        async for line in file:
            data.append(json.loads(line))
    random_indices = generate_random_indices(len(data), samples, test)
    data = [data[i] for i in random_indices]
    return data


async def check_solution(solution, test, entry_point):
    try:
        # 定义一个包含所有必要模块的全局字典
        global_dict = {
            'math': __import__('math'),
            'hashlib': __import__('hashlib'),
            're': __import__('re'),
            'List': List,
            'Dict': Dict,
            'Tuple': Tuple,
            'Optional': Optional,
            'Any': Any
        }
        # 执行解决方案
        exec(solution, global_dict)
        
        # 确保入口点函数已定义
        if entry_point not in global_dict:
            raise ValueError(f"函数 {entry_point} 在解决方案中未定义。")
        
        # 执行测试用例
        exec(test, global_dict)
        
        # 获取检查函数
        check = global_dict["check"]
        
        # 运行检查函数
        result = check()
        
        if result is None:
            result = (PASS, "解决方案通过了所有测试用例。")
    
    # except ValueError as ve:
    #     if "函数" in str(ve) and "在解决方案中未定义" in str(ve):
    #         raise
    except Exception as e:
        # 记录详细的错误信息
        error_message = f"错误: {str(e)}.\n 解决方案: {solution}.\n 测试: {test}"
        result = (FAIL, error_message)
        
        # 将错误信息写入error.log文件
        with open('error_mbpp.log', 'a', encoding='utf-8') as log_file:
            log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_message}\n")
    
    return result

async def evaluate_problem(data: dict, graph: Callable) -> Tuple[str, str, str, int, str]:
    max_retries = 5
    retries = 0

    while retries < max_retries:
        try:
            prediction = await graph(data["prompt"], data["entry_point"]) if graph else "None"
            cost = prediction[1]
            solution = prediction[0]
            ret = await check_solution(solution, data["test"], data["entry_point"]) 

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

    return data["prompt"], solution, ret[1], score, cost

async def evaluate_all_problems(data: List[dict], graph: Callable, max_concurrent_tasks: int = 50) -> List[Tuple[str, str, str, int, str]]:
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            return await evaluate_problem(problem, graph)

    tasks = [sem_evaluate(problem) for problem in data]

    return await tqdm_asyncio.gather(*tasks, desc="Evaluating MBPP problems", total=len(data))

def save_results_to_csv(results: List[Tuple[str, str, str, int, str]], path: str) -> Tuple[float, float]:
    df = pd.DataFrame(results, columns=["question", "prediction", "test_case_details", "score", "cost"])
    average_score = df["score"].mean()
    total_cost = df["cost"].max()

    output_file = f"{path}/{average_score:.5f}.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")
    return average_score, total_cost

async def mbpp_evaluation(graph: Callable, file_path: str, samples: int, path: str, test=False) -> Tuple[float, float]:
    data = await load_data(file_path, samples, test)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=25)
    average_score, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score on MBPP dataset: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, total_cost


async def load_file_data(file_path: str) -> List[dict]:
    data = []
    async with aiofiles.open(file_path, mode="r") as file:
        async for line in file:
            data.append(json.loads(line))
    return data

async def optimize_mbpp_evaluation(graph: Callable, file_path: str, path: str) -> Tuple[float, float]:
    data = await load_file_data(file_path)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=50)
    average_score, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score on MBPP dataset: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, total_cost