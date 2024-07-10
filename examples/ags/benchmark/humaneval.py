# -*- coding: utf-8 -*-
# @Date    : 7/7/2024 17:07 PM
# @Author  : didi
# @Desc    : test on human eval graph

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

async def sample_generate(id):
    case = get_human_eval_plus()[f"{id}"]
    solution_result = await solver(case['prompt'],ensemble_count=5)
    sample_dict = dict(task_id=case['task_id'], solution=solution_result['final_solution'])
    with open("samples.jsonl", mode='a') as f:
        f.write(json.dumps(sample_dict) + '\n')
    jsonl_ranker("samples.jsonl", "samples.jsonl")

async def samples_generate(mode:str):
    cases = list(get_human_eval_plus().values())
    file_lock = asyncio.Lock()
    
    async def solve_and_write(case, mode):
        try:
            if mode == 'llm':
                # solution_result = await generate_code_block(case['prompt'])
                solution_result = await generate_code(case['prompt'])
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
                async with aiofiles.open("samples.jsonl", mode='a') as f:
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
        for task_id in failed_tasks:
            try:
                await sample_generate(task_id) 
            except Exception as e:
                print(f"failure {task_id}")
    jsonl_ranker("samples.jsonl", "samples.jsonl")
    
    if not failed_tasks:
        if automatic_evalplus():
            unpassed_exapmle = extract_failure_tests()
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

def automatic_evalplus():
    """
    在命令行中自动执行 evalplus.evaluate --dataset humaneval --samples samples.jsonl --parallel 2 --base-only
    """
    command = [
        sys.executable,  # 使用当前 Python 解释器
        "-m",
        "evalplus.evaluate",
        "--dataset", "humaneval",
        "--samples", "samples.jsonl",
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
    
def extract_failure_tests(file_path:str = "/Users/trl/Github_project/MetaGPT-MathAI/samples_eval_results.json"):
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
# asyncio.run(samples_generate(mode='llm'))
# jsonl_ranker("samples.jsonl", "samples.jsonl")
# {"task_id": "HumanEval/101", "solution": "def words_string(s):\n    import re\n    return re.split(r'[,\\s]\\s*', s)"}