import os
import json
import time
import asyncio
import aiofiles
import threading
import pandas as pd
from typing import List, Tuple, Callable, Any, Optional, Dict
from datetime import datetime

from tqdm.asyncio import tqdm_asyncio
from examples.aflow.benchmark.utils import log_mismatch
from metagpt.actions.code_sanitize import sanitize
from examples.aflow.benchmark.utils import generate_random_indices

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


PASS = "PASS"
FAIL = "FAIL"

class TimeoutError(Exception):
    pass

def run_with_timeout(func, timeout):
    result = []
    stop_event = threading.Event()

    def target():
        try:
            result.append(func())
        except Exception as e:
            result.append(e)
        finally:
            stop_event.set()

    thread = threading.Thread(target=target)
    thread.start()
    is_timeout = not stop_event.wait(timeout)

    if is_timeout:
        # 线程仍在运行，我们无法强制终止它，但至少可以标记超时
        raise TimeoutError("Function execution timed out")

    if not result:
        return None
    if isinstance(result[0], Exception):
        raise result[0]
    return result[0]

def check_solution(solution, test, entry_point):

    solution = sanitize(code=solution, entrypoint=entry_point)
    print(test)
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
        
        # 运行检查函数，设置超时时间为120秒
        result = run_with_timeout(check, 15)
        
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

    expected_output = "\nCorrect Solution:\ndef " + data["code"]
    while retries < max_retries:
        try:
            prediction = await graph(data["prompt"], data["entry_point"]) if graph else "None"
            cost = prediction[1]
            solution = prediction[0]
            ret = check_solution(solution, data["test"], data["entry_point"]) 
            test_case_details = ret[1]
            expected_output = test_case_details + "\nCorrect Solution:" + data["code"]    
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

    return data["prompt"], solution, expected_output, score, cost

async def evaluate_all_problems(data: List[dict], graph: Callable, path:str="", max_concurrent_tasks: int = 50) -> List[Tuple[str, str, str, int, str]]:
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_evaluate(problem):
        async with semaphore:
            return await evaluate_problem(problem, graph, path)

    tasks = [sem_evaluate(problem) for problem in data]

    return await tqdm_asyncio.gather(*tasks, desc="Evaluating MBPP problems", total=len(data))

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

async def mbpp_evaluation(graph: Callable, file_path: str, samples: int, path: str, test=False) -> Tuple[float, float]:
    data = await load_data(file_path, samples, test)
    results = await evaluate_all_problems(data, graph, max_concurrent_tasks=25)
    average_score, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score on MBPP dataset: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    return average_score, total_cost


async def optimize_mbpp_evaluation(graph: Callable, file_path: str, path: str, va_list: List[int]) -> Tuple[float, float]:
    data = await load_file_data(file_path, va_list)
    results = await evaluate_all_problems(data, graph, path, max_concurrent_tasks=25)
    average_score, average_cost, total_cost = save_results_to_csv(results, path=path)
    print(f"Average score on MBPP dataset: {average_score:.5f}")
    print(f"Total Cost: {total_cost:.5f}")
    print(f"Average cost on MBPP dataset: {average_cost:.5f}")
    return average_score, average_cost, total_cost  