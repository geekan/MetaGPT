import asyncio

from metagpt.llm import LLM
from evalplus.data import get_human_eval_plus, write_jsonl
from examples.ags.w_action_node.graph import HumanEvalGraph
from examples.ags.w_action_node.operator import GenerateCode

generate_code = GenerateCode(llm=LLM())
solver = HumanEvalGraph(name="solver", llm=LLM(), criteria='correctness, efficiency, readability')



async def samples_generate_sequence():
    sample_list = []
    for case in get_human_eval_plus().values():
        solution_result = await solver(case['prompt'])
        sample_dict = dict(task_id=case['task_id'], solution=solution_result['final_solution'])
        sample_list.append(sample_dict)
    write_jsonl("samples.jsonl", sample_list)

async def samples_generate_ags():
    sample_list = []
    cases = list(get_human_eval_plus().values())
    
    async def solve_with_id(case):
        solution_result = await solver(case['prompt'])
        return case['task_id'], solution_result['final_solution']
    
    tasks = [solve_with_id(case) for case in cases]
    results = await asyncio.gather(*tasks)
    
    for task_id, solution in results:
        sample_dict = dict(task_id=task_id, solution=solution)
        sample_list.append(sample_dict)
    
    write_jsonl("samples.jsonl", sample_list)

    # humanevalgraph result (review & revise -> ensemble)
    # humaneval (base tests)
    # pass@1: 0.823
    # humaneval+ (base + extra tests)
    # pass@1: 0.774

    # deepseek result
    # humaneval (base tests)
    # pass@1: 0.841
    # humaneval+ (base + extra tests)
    # pass@1: 0.780

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

asyncio.run(samples_generate_llm())

