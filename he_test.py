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