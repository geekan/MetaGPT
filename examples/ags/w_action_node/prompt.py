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

# GENERATE_CODE_PROMPT = """
# Below is an instruction that describes a task, paired with an input that provides further context.
# Write a response that appropriately completes the request.

# ### Instruction:
# Write a program to perform the given task.

# Input:
# {problem_description}

# ### Response:
# """

GENERATE_CODE_PROMPT = """
You are an expert programmer tasked with solving a coding problem. Your goal is to write clean, efficient, and correct code that solves the given problem.

### Problem Description:
{problem_description}

### Instructions:
1. Read the problem description carefully.
2. If any part of the problem is unclear, state your assumptions.
3. Plan your approach before writing code.
4. Write a Python function that solves the problem.
5. Include clear comments to explain your logic.
6. Ensure your code handles edge cases and potential errors.
7. If time complexity is a concern, optimize your solution and explain your optimization.

Please maintain the JSON format in your response.
### Your Response: 
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

FU_ENSEMBLE_PROMPT = """
### Given problem

{problem_description}

### We've got a list of solutions

<solutions>
{solutions}
</solutions>

### Instructions
Based on the given problem and solution candidates:

1. Analyze the pros and cons of each candidate solution
2. Consider how to integrate reasonable parts from different solutions
3. Formulate a more comprehensive and effective solution
"""

MD_ENSEMBLE_PROMPT = """
### Given problem

{problem_description}

### We've got a list of solutions

<solutions>
{solutions}
</solutions>

### Instructions
Carefully analyze the given problem and the list of solution candidates. Your task is to determine the best answer based solely on how correctly and effectively it addresses the problem. Follow these steps:

1. Thoroughly examine each solution.
2. Evaluate their relevance and effectiveness in solving the problem.
3. Compare the solutions to identify the most suitable one.
4. Provide your final decision by writing the chosen solution letter (e.g., B).

Please maintain the JSON format in your response.
"""

