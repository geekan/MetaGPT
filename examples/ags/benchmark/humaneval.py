import os
import time
import json
import asyncio
import aiofiles
import threading
from datetime import datetime
from typing import List, Tuple, Callable, Dict, Any, Optional

import pandas as pd
from tqdm.asyncio import tqdm_asyncio

from examples.ags.benchmark.utils import generate_random_indices
from examples.ags.benchmark.utils import log_mismatch


async def load_data(file_path: str, samples=1, test=False) -> List[dict]:
    data = []
    async with aiofiles.open(file_path, mode="r") as file:
        async for line in file:
            data.append(json.loads(line))
    random_indices = generate_random_indices(len(data), samples, test)
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

# async def check_solution(solution, test, entry_point):

#     print(f"solution: {solution}")

#     try:
#         # 定义一个包含所有必要模块的全局字典
#         global_dict = {
#             'math': __import__('math'),
#             'hashlib': __import__('hashlib'),
#             're': __import__('re'),
#             'List': List,
#             'Dict': Dict,
#             'Tuple': Tuple,
#             'Optional': Optional,
#             'Any': Any
#         }
#         if entry_point == "decode_cyclic":
#             solution = "\n\ndef encode_cyclic(s: str):\n    \"\"\"\n    returns encoded string by cycling groups of three characters.\n    \"\"\"\n    # split string to groups. Each of length 3.\n    groups = [s[(3 * i):min((3 * i + 3), len(s))] for i in range((len(s) + 2) // 3)]\n    # cycle elements in each group. Unless group has fewer elements than 3.\n    groups = [(group[1:] + group[0]) if len(group) == 3 else group for group in groups]\n    return \"\".join(groups)" + "\n\n" + solution
#         elif entry_point == "decode_shift":
#             solution = "\n\ndef encode_shift(s: str):\n    \"\"\"\n    returns encoded string by shifting every character by 5 in the alphabet.\n    \"\"\"\n    return \"\".join([chr(((ord(ch) + 5 - ord(\"a\")) % 26) + ord(\"a\")) for ch in s])\n\n\n" + solution
#         elif entry_point == "find_zero":
#             solution = "\n\ndef poly(xs: list, x: float):\n    return sum(coeff * (x ** i) for i, coeff in enumerate(xs))\n\n" + solution
#         # 执行解决方案
#         exec(solution, global_dict)
        
#         # 确保入口点函数已定义
#         if entry_point not in global_dict:
#             raise ValueError(f"函数 {entry_point} 在解决方案中未定义。")
        
#         # 执行测试用例
#         exec(test, global_dict)
        
#         # 获取检查函数
#         check = global_dict["check"]
        
#         # 运行检查函数
#         result = check(global_dict[entry_point])
        
#         if result is None:
#             result = (PASS, "解决方案通过了所有测试用例。")
    
#     except Exception as e:
#         # 记录详细的错误信息
#         error_message = f"错误: {str(e)}.\n 解决方案: {solution}.\n 测试: {test}"
#         result = (FAIL, error_message)
        
#         # 将错误信息写入error.log文件
#         with open('error.log', 'a', encoding='utf-8') as log_file:
#             log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_message}\n")
    
#     return result

PASS = "PASS"
FAIL = "FAIL"

class TimeoutError(Exception):
    pass

def run_with_timeout(func, args, timeout):
    result = []
    def target():
        try:
            result.append(func(*args))
        except Exception as e:
            result.append(e)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError("Function execution timed out")
    if isinstance(result[0], Exception):
        raise result[0]
    return result[0]

def check_solution(solution, test, entry_point):
    print(f"solution: {solution}")

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
        
        # 运行检查函数，设置超时时间为5秒
        result = run_with_timeout(check, (global_dict[entry_point],), 120)
        
        if result is None:
            result = (PASS, "解决方案通过了所有测试用例。")
    
    except TimeoutError:
        result = (FAIL, "执行超时。请检查您的解决方案是否包含无限循环或过于耗时的操作。")
    except Exception as e:
        # 记录详细的错误信息
        error_message = f"错误: {str(e)}.\n 解决方案: {solution}.\n 测试: {test}"
        result = (FAIL, error_message)
        
        # 将错误信息写入error.log文件
        with open('error.log', 'a', encoding='utf-8') as log_file:
            log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_message}\n")
    
    return result


async def evaluate_problem(data: dict, graph: Callable, path) -> Tuple[str, str, str, int, str]:
    max_retries = 5
    retries = 0

    # prediction = await graph(data["prompt"], data["entry_point"]) if graph else "None"
    # cost = prediction[1]  
    # solution = prediction[0]
    # ret = check_solution(solution, data["test"], data["entry_point"])
    # test_case_details = ret[1]
    # expected_output = test_case_details + "\nCorrect Solution:\ndef " + data["entry_point"] + "(params you should put here):" + "\n\n" + data["canonical_solution"]
    # score = 1 if ret[0] == PASS else 0

    while retries < max_retries:
        try:
            prediction = await graph(data["prompt"], data["entry_point"]) if graph else "None"
            cost = prediction[1]  
            solution = prediction[0]
            ret = check_solution(solution, data["test"], data["entry_point"])
            test_case_details = ret[1]
            expected_output = test_case_details + "\nCorrect Solution:\ndef " + data["entry_point"] + "(params you should put here):" + "\n\n" + data["canonical_solution"]
            score = 1 if ret[0] == PASS else 0

            if score == 0:
                log_mismatch(data["prompt"], expected_output, solution, score, path)
            break

        except Exception as e:
            retries += 1
            print(f"Error generating prediction: {e}. Retrying... ({retries}/{max_retries})")

            if retries == max_retries:
                print("Maximum retries reached. Skipping this sample.")
                solution = None
                ret = (FAIL, [])
                score = 0
                cost = 0 
                break

    return data["prompt"], solution, expected_output, score, cost  # 修改返回值以包含cost

async def evaluate_all_problems(data: List[dict], graph: Callable, path:str="", max_concurrent_tasks: int = 50) -> List[Tuple[str, str, str, int, str]]:
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            return await evaluate_problem(problem, graph, path)

    tasks = [sem_evaluate(problem) for problem in data]

    return await tqdm_asyncio.gather(*tasks, desc="Evaluating HumanEval problems", total=len(data))

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

async def humaneval_evaluation(graph: Callable, file_path: str, samples: int, path: str, test=False) -> Tuple[float, float]:
    data = await load_data(file_path, samples, test=test)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=50)
    average_score, average_cost, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score on HumanEval dataset: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    print(f"Average cost on HumanEval dataset: {average_cost:.5f}")
    return average_score, total_cost  # 修改返回值以包含total_cost


async def optimize_humaneval_evaluation(graph: Callable, file_path: str, path: str, va_list: List[int]) -> Tuple[float, float, float]:
    data = await load_file_data(file_path, va_list)
    results = await evaluate_all_problems(data, graph, path, max_concurrent_tasks=25)
    average_score, average_cost, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score on HumanEval dataset: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    print(f"Average cost on HumanEval dataset: {average_cost:.5f}")
    return average_score, average_cost, total_cost  

# TODO HumanEval 主实验后续任务

# 1. 修改optimized中的内容，让优化代码能够跑起来
# 2. 启动主实验