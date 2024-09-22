import json
import asyncio
import aiofiles
import pandas as pd
from typing import List, Tuple, Callable, Dict, Any, Optional
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

# async def check_solution(solution, test_cases, entry_point):
#     # Define a local dictionary to execute the solution
#     local_dict = {}
#     exec("from typing import List, Tuple, Callable, Dict\n\n" + solution, {}, local_dict)

#     # Ensure the entry point function is defined
#     if entry_point not in local_dict:
#         raise ValueError(f"Function {entry_point} is not defined in the solution.")

#     details = [False for _ in range(len(test_cases))]

#     # Check each test case
#     for i, test in enumerate(test_cases):
#         # Replace 'candidate' with the actual function call
#         test_expr = test.replace("candidate", entry_point)
#         try:
#             # Evaluate the test case
#             if eval(test_expr, {}, local_dict):
#                 details[i] = True
#         except Exception as e:
#             print(f"Error evaluating test case '{test}': {e}")

#     if all(details):
#         return PASS, details

#     return FAIL, details

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
        if entry_point == "decode_cyclic":
            solution = "\n\ndef encode_cyclic(s: str):\n    \"\"\"\n    returns encoded string by cycling groups of three characters.\n    \"\"\"\n    # split string to groups. Each of length 3.\n    groups = [s[(3 * i):min((3 * i + 3), len(s))] for i in range((len(s) + 2) // 3)]\n    # cycle elements in each group. Unless group has fewer elements than 3.\n    groups = [(group[1:] + group[0]) if len(group) == 3 else group for group in groups]\n    return \"\".join(groups)" + "\n\n" + solution
        elif entry_point == "decode_shift":
            solution = "\n\ndef encode_shift(s: str):\n    \"\"\"\n    returns encoded string by shifting every character by 5 in the alphabet.\n    \"\"\"\n    return \"\".join([chr(((ord(ch) + 5 - ord(\"a\")) % 26) + ord(\"a\")) for ch in s])\n\n\n" + solution
        elif entry_point == "find_zero":
            solution = "\n\ndef poly(xs: list, x: float):\n    return sum(coeff * (x ** i) for i, coeff in enumerate(xs))\n\n" + solution
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
        result = check(global_dict[entry_point])
        
        if result is None:
            result = (PASS, "解决方案通过了所有测试用例。")
    
    except Exception as e:
        # 记录详细的错误信息
        error_message = f"错误: {str(e)}.\n 解决方案: {solution}.\n 测试: {test}"
        result = (FAIL, error_message)
        
        # 将错误信息写入error.log文件
        with open('error.log', 'a', encoding='utf-8') as log_file:
            log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_message}\n")
    
    return result

async def evaluate_problem(data: dict, graph: Callable) -> Tuple[str, str, str, int, str]:
    max_retries = 5
    retries = 0

    while retries < max_retries:
        try:
            prediction = await graph(data["prompt"], data["entry_point"]) if graph else "None"
            cost = prediction[1]  # 添加这行来获取cost
            solution = prediction[0]  # 修改这行以获取实际的预测结果
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
                cost = 0  # 添加这行来处理错误情况下的cost
                break

    return data["prompt"], solution, ret[1], score, cost  # 修改返回值以包含cost

async def evaluate_all_problems(data: List[dict], graph: Callable, max_concurrent_tasks: int = 50) -> List[Tuple[str, str, str, int, str]]:
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            return await evaluate_problem(problem, graph)

    tasks = [sem_evaluate(problem) for problem in data]

    return await tqdm_asyncio.gather(*tasks, desc="Evaluating HumanEval problems", total=len(data))

import os
import time
import json

def save_results_to_jsonl(results: List[Tuple[str, str, str, int, str]], path: str) -> Tuple[float, float]:
    avg_score = 0
    total_cost = 0  # 添加这行来计算总cost
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
                        "cost": result[4],  # 添加这行来包含cost
                    }
                )
                + "\n"
            )
            avg_score += result[3]
            total_cost += float(result[4])  # 添加这行来累加cost
    print(f"save to {full_path}")
    avg_score /= len(results)
    # 从full_path中读取所有结果,选择得分最高的
    with open(full_path, 'r') as f:
        all_results = [json.loads(line) for line in f]
    max_result = max(all_results, key=lambda x: x['cost'])
    total_cost = max_result['cost']

    return round(avg_score, 5), round(total_cost, 5)  # 修改返回值以包含total_cost

async def humaneval_evaluation(graph: Callable, file_path: str, samples: int, path: str, test=False) -> Tuple[float, float]:
    data = await load_data(file_path, samples, test=test)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=50)
    average_score, total_cost = save_results_to_jsonl(results, path=path)
    print(f"Average score on HumanEval dataset: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, total_cost  # 修改返回值以包含total_cost


async def load_file_data(file_path: str) -> List[dict]:
    data = []
    async with aiofiles.open(file_path, mode="r") as file:
        async for line in file:
            data.append(json.loads(line))
    return data

async def optimize_humaneval_evaluation(graph: Callable, file_path: str, path: str) -> Tuple[float, float]:
    data = await load_file_data(file_path)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=10)
    average_score, total_cost = save_results_to_jsonl(results, path=path)
    print(f"Average score on HumanEval dataset: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, total_cost  