import asyncio
from metagpt.llm import LLM
from examples.ags.benchmark.humaneval import sample_generate, samples_generate, extract_failure_tests, automatic_evalplus
from examples.ags.w_action_node.utils import jsonl_ranker

# asyncio.run(sample_generate('HumanEval/101'))
# asyncio.run(sample_generate('HumanEval/1'))
asyncio.run(samples_generate(mode='ags'))
# jsonl_ranker("samples.jsonl", "samples.jsonl")


# if automatic_evalplus():
#     unpassed_exapmle = extract_failure_tests()
#     print(unpassed_exapmle)

# unpassed_exapmle = extract_failure_tests()
# print(unpassed_exapmle)

# failure_list = ['HumanEval/0', 'HumanEval/1', 'HumanEval/7', 'HumanEval/16', 'HumanEval/24', 'HumanEval/31', 'HumanEval/40', 'HumanEval/56', 'HumanEval/67', 'HumanEval/74', 'HumanEval/83', 'HumanEval/86', 'HumanEval/87', 'HumanEval/90', 'HumanEval/95', 'HumanEval/101', 'HumanEval/104', 'HumanEval/113', 'HumanEval/125', 'HumanEval/132', 'HumanEval/135', 'HumanEval/140', 'HumanEval/143', 'HumanEval/145', 'HumanEval/154', 'HumanEval/161']

# for example in failure_list:
#     asyncio.run(sample_generate(example))