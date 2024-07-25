import asyncio
import json
from metagpt.llm import LLM
from evalplus.data import get_human_eval_plus, write_jsonl
from examples.ags.benchmark.humaneval import sample_generate, samples_generate, extract_failure_tests, automatic_evalplus
from examples.ags.w_action_node.utils import jsonl_ranker, llm_extract_test_case
from examples.ags.w_action_node.graph import HumanEvalGraph
# 132 141 136 80 73
# asyncio.run(sample_generate('HumanEval/118',result_path="llm_based_8.jsonl",mode="llm"))
asyncio.run(samples_generate(mode='llm',result_path="llm_based_100.jsonl"))
# jsonl_ranker("samples.jsonl", "samples.jsonl")

# result_path = "ags_based_6.jsonl"
# if automatic_evalplus(result_path):
#     unpassed_exapmle = extract_failure_tests(result_path[:-6]+"_eval_results.json")
#     print(unpassed_exapmle)

# unpassed_exapmle = extract_failure_tests(file_path="2_eval_results.json")
# print(unpassed_exapmle)

# for example in failure_list:
#     asyncio.run(sample_generate(example))

# TODO 抽取Public Test没搞完，先用几个测试跑一下流程
# from evalplus.data import get_human_eval_plus

# id_list = [87, 95, 107, 112, 127, 136, 148, 155]
# id_list = [155]
# cases_id = [f"HumanEval/{case_id}" for case_id in id_list]
# cases = {case_id: get_human_eval_plus()[case_id]['prompt'] for case_id in cases_id}
# async def main(cases):
#     try:
#         tasks = [llm_extract_test_case(case_id, case) for case_id, case in cases.items()]
#         results = await asyncio.gather(*tasks)
#     except:
#         failed_tasks = [task_id for task_id in results if task_id is not None]
#         print(failed_tasks)
#     return results

# asyncio.run(main(cases))

# [72, 80, 82, 87, 90, 95, 107, 109, 112, 124, 126, 127, 128, 132, 134, 136, 137, 138, 148, 154, 155]

# case_prompt= get_human_eval_plus()["HumanEval/136"]['prompt']
# solver = HumanEvalGraph(name="solver", llm=LLM(), criteria='correctness, efficiency, readability', vote_count=1)
# result = asyncio.run(solver.alpha_codium(problem_id="HumanEval/136", problem=case_prompt, ensemble_count=1))