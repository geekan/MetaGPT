import json
import asyncio
import aiofiles
from metagpt.llm import LLM
from evalplus.data import get_human_eval_plus, write_jsonl
from examples.ags.w_action_node.utils import jsonl_ranker
from examples.ags.w_action_node.graph import HumanEvalGraph
from examples.ags.w_action_node.operator import GenerateCode

generate_code = GenerateCode(llm=LLM())

solver = HumanEvalGraph(name="solver", llm=LLM(), criteria='correctness, efficiency, readability', vote_count=5)

async def sample_generate(id):
    case = get_human_eval_plus()[f"{id}"]
    solution_result = await solver(case['prompt'],ensemble_count=3)
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
                solution_result = await generate_code(case['prompt'])
                sample_dict = {
                'task_id': case['task_id'],
                'solution': solution_result['code_solution']
                }
            elif mode == "ags":
                solution_result = await solver(case['prompt'], ensemble_count=3)
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
        solution_result =  await generate_code(case['prompt'])
        return case['task_id'], solution_result['code_solution']
    
    tasks = [solve_with_id(case) for case in cases]
    results = await asyncio.gather(*tasks)
    
    for task_id, solution in results:
        sample_dict = dict(task_id=task_id, solution=solution)
        sample_list.append(sample_dict)
    
    write_jsonl("samples.jsonl", sample_list)

# asyncio.run(sample_generate('HumanEval/101'))
# asyncio.run(samples_generate_llm())
asyncio.run(samples_generate(mode='ags'))
# jsonl_ranker("samples.jsonl", "samples.jsonl")



