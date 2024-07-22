# -*- coding: utf-8 -*-
# @Date    : 7/7/2024 17:07 PM
# @Author  : didi
# @Desc    : test on human eval graph

import os
import json
import subprocess
import sys
import asyncio
import aiofiles
from metagpt.llm import LLM
from evalplus.data import get_human_eval_plus, write_jsonl
from examples.ags.w_action_node.utils import jsonl_ranker
from examples.ags.w_action_node.graph import HumanEvalGraph
from examples.ags.w_action_node.operator import GenerateCode, GenerateCodeBlock

generate_code = GenerateCode(llm=LLM())
generate_code_block = GenerateCodeBlock(llm=LLM())

solver = HumanEvalGraph(name="solver", llm=LLM(), criteria='correctness, efficiency, readability', vote_count=5)

async def sample_generate(id, result_path:str="samples.jsonl",mode:str="ags"):
    case = get_human_eval_plus()[f"{id}"]
    if mode == "ags":
        solution_result = await solver(case['prompt'],ensemble_count=5)
        sample_dict = dict(task_id=case['task_id'], solution=solution_result['final_solution'])
    else:
        solution_result =  await generate_code_block(case['prompt'])
        sample_dict = dict(task_id=case['task_id'], solution=solution_result['code_solution'])
    with open(result_path, mode='a') as f:
        f.write(json.dumps(sample_dict) + '\n')
    jsonl_ranker(result_path, result_path)

async def samples_generate(mode:str, result_path:str="samples.jsonl"):
    cases = list(get_human_eval_plus().values())
    file_lock = asyncio.Lock()
    
    async def solve_and_write(case, mode):
        try:
            if mode == 'llm':
                solution_result = await generate_code_block(case['prompt'])
                # solution_result = await generate_code(case['prompt'])
                sample_dict = {
                'task_id': case['task_id'],
                'solution': solution_result['code_solution']
                }
            elif mode == "ags":
                solution_result = await solver(case['prompt'], ensemble_count=5)
                sample_dict = {
                'task_id': case['task_id'],
                'solution': solution_result['final_solution']
                }

            async with file_lock:
                async with aiofiles.open(result_path, mode='a') as f:
                    await f.write(json.dumps(sample_dict) + '\n')
            return None

        except Exception as e: 
            print(e)
            return case['task_id']

    tasks = [solve_and_write(case, mode) for case in cases]
    results = await asyncio.gather(*tasks)
    failed_tasks = [task_id for task_id in results if task_id is not None]

    # TODO 这个地方还是不够自动化
    if failed_tasks:
        print(failed_tasks)
        if mode == 'llm':
            for task_id in failed_tasks:
                case = get_human_eval_plus()[task_id]
                for _ in range(3):
                    try:
                        solution_result = await generate_code_block(case['prompt'])
                        task_dict = {
                        'task_id': case['task_id'],
                        'solution': solution_result['code_solution']
                        }
                        with open(result_path, mode='a') as f:
                            f.write(json.dumps(task_dict) + '\n')
                        failed_tasks.remove(task_id)
                        break
                    except Exception as e:
                        print(f"{e} \n failure {task_id}")
        elif mode == "ags":
            for task_id in failed_tasks:
                try:
                    await sample_generate(task_id,result_path) 
                except Exception as e:
                    print(f"failure {task_id}")
    jsonl_ranker(result_path, result_path)
    
    if not failed_tasks:
        # 自动 sanitize
        result_path = automatic_sanitize(result_path)
        if automatic_evalplus(result_path):
            eval_path = result_path[:-6]+"_eval_results.json"
            unpassed_exapmle = extract_failure_tests(eval_path)
            print(unpassed_exapmle)
    else:
        print(failed_tasks)

async def samples_generate_ags():
    sample_list = []
    cases = list(get_human_eval_plus().values())
    
    async def solve_with_id(case):
        solution_result = await solver(case['prompt'], ensemble_count=3)
        return case['task_id'], solution_result['final_solution']
    
    tasks = [solve_with_id(case) for case in cases]
    results = await asyncio.gather(*tasks)
    
    for task_id, solution in results:
        sample_dict = dict(task_id=task_id, solution=solution)
        sample_list.append(sample_dict)
    
    write_jsonl("samples.jsonl", sample_list)

async def samples_generate_llm():
    sample_list = []
    cases = list(get_human_eval_plus().values())
    
    async def solve_with_id(case):
        solution_result =  await generate_code_block(case['prompt'])
        # solution_result =  await generate_code(case['prompt'])
        return case['task_id'], solution_result['code_solution']
    
    tasks = [solve_with_id(case) for case in cases]
    results = await asyncio.gather(*tasks)
    
    for task_id, solution in results:
        sample_dict = dict(task_id=task_id, solution=solution)
        sample_list.append(sample_dict)
    
    write_jsonl("samples.jsonl", sample_list)

def automatic_sanitize(result_path: str = "samples.jsonl"):
    """
    在命令行中自动执行 evalplus.sanitize --samples result_path
    返回result_path前缀加上"-sanitized.jsonl"
    """
    command = ["evalplus.sanitize", "--samples", result_path]
    
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"执行命令时出错: {e}")
        return None
    
    # 构建sanitized文件路径
    base_name = os.path.splitext(result_path)[0]
    sanitized_path = f"{base_name}-sanitized.jsonl"
    
    return sanitized_path
def automatic_evalplus(result_path:str ="samples.jsonl"):
    """
    在命令行中自动执行 evalplus.evaluate --dataset humaneval --samples samples.jsonl --parallel 2 --base-only
    """
    command = [
        sys.executable,  # 使用当前 Python 解释器
        "-m",
        "evalplus.evaluate",
        "--dataset", "humaneval",
        "--samples", result_path,
        "--parallel", "2",
        "--base-only"
    ]
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("输出:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("错误输出:", e.stderr)
        return False
    
def extract_failure_tests(file_path:str = "samples_eval_results.json"):
    with open(file_path, 'r') as f:
        task_results = json.load(f)

    failed_tests = []
    
    for task in task_results['eval'].values():
        if task[0]["base_status"] == "fail":
            failed_test = {
                "task_id": task[0]["task_id"],
                # "solution": task["solution"],
                # "fail_tests": task["base_fail_tests"]
            }
            failed_tests.append(failed_test)
    print(len(failed_tests))
    
    return failed_tests


# asyncio.run(sample_generate('HumanEval/101'))
# asyncio.run(samples_generate(mode='ags'))
# jsonl_ranker("samples.jsonl", "samples.jsonl")
# {"task_id": "HumanEval/101", "solution": "def words_string(s):\n    import re\n    return re.split(r'[,\\s]\\s*', s)"}

