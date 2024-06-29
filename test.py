import asyncio
from examples.ags.w_action_node.graph import HumanEvalGraph
from metagpt.llm import LLM 

human_eval_example = """
from typing import List\n\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\" Check if in given list of numbers, are any two numbers closer to each other than\n    given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n    True\n    \"\"\"\n
"""

solver = HumanEvalGraph(name="solver", llm=LLM(), criteria='correctness, efficiency, readability')

final_result = asyncio.run(solver(human_eval_example))
print(final_result)