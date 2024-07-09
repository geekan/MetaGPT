# -*- coding: utf-8 -*-
# @Date    : 6/26/2024 17:07 PM
# @Author  : didi
# @Desc    : prompts of operators

# TODO PromptBreeder 评分是怎么做的？
# TODO 评估案例 GSM-8K 直接拿的DataSet
# 
# 

GENERATE_PROMPT = """
Generate Solution for the following problem: {problem_description}
"""

GENERATE_CODE_PROMPT = """
Below is an instruction that describes a task, paired with an input that provides further context.
Write a response that appropriately completes the request.

### Instruction:
Write a program to perform the given task.

Input:
{problem_description}

### Response:
"""
# GENERATE_CODE_PROMPT = """
# Generate Code Solution for the following problem: {problem_description}
# """

REVIEW_PROMPT = """
For the question described as {problem_description},
please review the following solution: {solution}, and provide a review result in boolean format.
If you believe the solution is capable of resolving the issue, return True; otherwise, return False, and include your comments
"""

REVISE_PROMPT = """
For the question described as {problem_description},
please evaluate and revise the solution provided: {solution}, taking into account the review feedbacks: {feedback}."
Then output the revised solution.
"""

ENSEMBLE_PROMPT = """
For the question described as {problem_description}, Solutions: {solutions}
Please select the solution that appears most frequently from these options and ensemble this to provide best solution.
"""

MD_ENSEMBLE_PROMPT = """
# Context
For the question described as {problem_description}, 
Solutions can be seen below: 
{solutions}

# Instruction
Based on the problem and solution candidates, carefully analyze which is the best answer. Focus solely on the correctness of the solution in addressing the problem.
Provide your final decision by writing the chosen solution number (e.g., A).
"""