# -*- coding: utf-8 -*-
# @Date    : 6/26/2024 17:07 PM
# @Author  : didi
# @Desc    : prompts of operators


GENERATE_PROMPT = """
Generate Solution for the following problem: {problem_description}
"""

GENERATE_CODE_PROMPT = """
Generate Code Solution for the following problem: {problem_description}
"""

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
