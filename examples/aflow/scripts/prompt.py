# -*- coding: utf-8 -*-
# @Date    : 6/26/2024 17:07 PM
# @Author  : didi
# @Desc    : prompts of operators

CONTEXTUAL_GENERATE_PROMPT = """
Generate Solution for the following problem: 

## Problem Description
{problem_description}

## Thought
{thought}
"""

GENERATE_CODEBLOCK_PROMPT = """
Please provide a self-contained  Python script that solves the following problem in a markdown code block:

{problem_description}

When creating your solution:
1. Consider all edge cases and boundary conditions.
2. Avoid oversimplification - address all aspects of the problem.
3. Ensure your logic covers all stated requirements.
4. Avoid adding additional test cases beyond those provided in the problem description.
"""

FORMAT_PROMPT = """
For the question described as {problem_description},
please extract a short and concise answer contains only one word/few words from the following solution: {solution}.
Make sure there are no additional comments or explanations in your response.
"""

REVIEW_PROMPT = """
For the question described as {problem_description},
please review the following solution: {solution}, and provide a review result in boolean format.
```
You will be reviewing the problem-solving process of another AI assistant that has answered a mathematical question. Your task is to evaluate the solution and provide a detailed review for refinement. Follow these steps:
<step1>
Carefully read through the original question and entire solution, paying close attention to the relevant concepts, thinking process, calculations, and final result. Assess whether the solution is clear, logical, and well-organized. Write your initial review in <initialReview> tags.
</step1>
<step2>
Evaluate the reasoning and logic behind the solution. Ensure that the thinking process is clear, coherent, and mathematically sound. If you find any areas that need clarification or improvement, provide your suggestions inside <reasoningFeedback> tags.
</step2>
<step3>
Re-do the calculations presented in the <calculation> section **carefully and step-by-step** to verify the accuracy. Break down the calculations into the simplest possible steps and check each step for errors. You must not be careless and treat every part with rigor. Don't neglect checking any calculation part of the solution process. If you find any mistakes, note them down inside <calculationErrors> tags.
</step3>
<step4>
Provide an overall assessment of the solution's thoroughness, accuracy, and clarity inside <overallAssessment> tags. Highlight the strengths and weaknesses of the solution and offer suggestions for improvement, if any.
</step4>
use XML tags to present your complete evaluation, including initial review, calculation errors, reasoning feedback, and overall assessment, in a well-organized and easy-to-follow format.
Remember to be thorough, constructive, and professional in your review. Your goal is to help improve the quality and accuracy of the mathematical problem-solving process.
```
If you believe the solution is capable of resolving the issue, return True; otherwise, return False, and include your comments
"""

REVISE_PROMPT = """
For the question described as {problem_description},
please evaluate and revise the solution provided: {solution}, taking into account the review feedbacks: {feedback}."
Then output the revised solution.
"""

MD_ENSEMBLE_PROMPT = """
You are given a problem:
{problem_description}

Here is a list of possible solutions to the problem:
{solutions}

Using the inputs above, your goal is to choose the best solution to the problem.
The main consideration is that the solution can fully solve the problem in a correct and robust manner.
Provide your final decision by writing the chosen solution letter.

Please follow the required format in your response.
"""

SC_ENSEMBLE_PROMPT = """
I have generated the following solutions to the question: {problem_description}

{solutions}

Evaluate these solutions.
Select the most consistent solution based on majority consensus.
Give your answer with a single id of solution (without anything else).
"""

REFLECTION_ON_PUBLIC_TEST_PROMPT = """
Given a code problem and a python code solution which failed to pass test or execute, you need to analyze the reason for the failure and propose a better code solution.: 
### problem
{problem}

### Code Solution
{solution}

### Execution Result
{exec_pass}

#### Failed Test Case
{test_fail}

Please provide a reflection on the failed test cases and code solution, followed by a better code solution without any additional text or test cases.
"""

PYTHON_CODE_VERIFIER_PROMPT = """You are a professional Python programmer. Your task is to write Python code based on the user's request. Make sure to add appropriate explanations and your personal thought process to your code. Additionally, all code should be encapsulated in Python code blocks.

The packages you can use include: numpy, scipy, pandas, sympy, statsmodels, scikit-learn. If you attempt to import another external package and encounter an error, do not say it cannot be imported. Instead, try to write new code that avoids this issue.

Always output complete code rather than just giving suggestions or partial modifications, as your code will be executed directly. If immediate execution is required to check for possible errors, include test cases in the code.

In your response, only the code that needs to be run should be wrapped in multi-line code blocks. No other multi-line code blocks should appear. Your code needs to print the output after execution. Your code should not print error messages.

Problem description: {problem}
Please write Python code to solve this problem.
"""
