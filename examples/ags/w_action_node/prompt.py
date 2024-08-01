# -*- coding: utf-8 -*-
# @Date    : 6/26/2024 17:07 PM
# @Author  : didi
# @Desc    : prompts of operators

GENERATE_PROMPT = """
Generate Solution for the following problem: {problem_description}
"""

GENERATE_CODE_PROMPT = """
You are an expert programmer tasked with solving a coding problem.

### Problem Description
{problem_description}

### Instructions
The above is an incomplete Python code fragment. Return the complete and correct code with no additional text.
Please maintain the JSON format in your response.
### Your Response 
"""

GENERATE_CODEBLOCK_REPHRASE_PROMPT = """
Please provide a self-contained  Python script that solves the following problem in a markdown code block:

### Problem Description
{problem_description}

### self reflection on the problem
{rephrase_problem}

When creating your solution:
1. Consider all edge cases and boundary conditions.
2. Avoid oversimplification - address all aspects of the problem.
3. Ensure your logic covers all stated requirements.
4. Avoid adding additional test cases beyond those provided in the problem description.
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
You are given a coding problem:
{problem_description}

Here is a list of possible solutions to the problem:
{solutions}

Using the inputs above, your goal is to choose the best solution to the code contest problem.
Don't just pick the most efficient solution. The main consideration is that the solution can fully solve the problem in a correct and robust manner.
Provide your final decision by writing the chosen solution letter (e.g., B).

Please maintain the JSON format in your response.
"""

DE_ENSEMBLE_TXT_FORMAT_PROMPT = """
Now please output your answer in json format, with the format as follows:
    {\"Reason\": \"\", \"debate_answer\": \"the capital letter corresponding to the answer\"}.
Please strictly output in JSON format, do not output irrelevant content. """

DE_ENSEMBLE_CODE_FORMAT_PROMPT = """
Now please output your answer in json format, with the format as follows:
{
    "reason":"<why do it this way>",
    "code_solution":"<the solution you think is appropriate, expressed in code>"
}
Please strictly output in JSON format, do not output irrelevant content. """

DE_ENSEMBLE_ANGEL_PROMPT = """
Do you agree with my perspective? Please provide your reasons and answer.
"""

DE_ENSEMBLE_DEVIL_PROMPT = """
You agree with my answer 90% of the time and have almost no reservations. Affirm your agreement, share any additional thoughts if you have them, and conclude with the capital letter corresponding to your answer at the end of your response.
"""

DE_ENSEMBLE_JUDGE_FINAL_PROMPT = """
You, as the moderator, will evaluate both sides' answers and determine your
            preference for an answer candidate. Please summarize your reasons for supporting affirmative/negative side and
            give the final answer that you think is correct to conclude the debate. Now please output your answer in json format, with the format as follows:
            {\"Reason\": \"\", \"debate_answer\": \"the capital letter corresponding to the answer\"}.
            Please strictly output in JSON format, do not output irrelevant content.
"""

DE_ENSEMBLE_JUDGE_UNIVERSAL_PROMPT = """
You, as the moderator, will evaluate both sides' answers and determine if there is a clear
            preference for an answer candidate. If so, please summarize your reasons for supporting affirmative/negative side and
            give the final answer that you think is correct, and the debate will conclude. If not, the debate will continue to
            the next round. Now please output your answer in json format, with the format as follows:
            {\"Whether there is a preference\": \"Yes or No\", \"Supported Side\": \"Affirmative or Negative\",
            \"Reason\": \"\", \"debate_answer\": \"the capital letter corresponding to the answer\"}.
            Please strictly output in JSON format, do not output irrelevant content
"""

REPHRASE_ON_PROBLEM_PROMPT = """
You are given a code contest problem:

### problem
{problem_description}

### instrcutions
Given the code contest problem, Your Goal is:
Reflect on the problem, and describe it in your own words, in bullet points. Pay attention to small details, nuances, notes and examples in the problem description.

"""

REFLECTION_ON_PUBLIC_TEST_PROMPT = """
You are given a code contest problem, and a self-reflection on the problem: 
### problem
{problem_description}


### self reflection on the problem
{rephrase_problem}


A Python code solution was generated for the problem:
### Code Solution
{code_solution}


This section of the code execution result is
### Execution Result
{exec_pass}


However, when running the following input example, the code solution above failed to produce the expected output:
#### Failed Test Case
{test_fail}

Your goal is to analyze the code solution and the error, and propose a fixed code which will produce the expected output for the provided test input.
The fixed code should keep the solution robust, and work for all other input examples as well.
Make sure the fixed code has a reasonable runtime - less than three seconds on a modern computer, given the problem constraints for large input.
"""

EXTRACT_CASE_PROMPT = """
You are given a coding problem, and you need to extract the test cases from the problem description.

## Problem Description
{problem_description}

Your task is to extract test cases from the above description and convert them into Python assert statements (as strings). These statements should be returned in a list for testing purposes.

Example:
Input:
>>> has_close_elements([1.0, 2.0, 3.0], 0.5)
False
>>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
True

Output:
[
    "assert candidate([1.0, 2.0, 3.0], 0.5) == False",
    "assert candidate([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True"
]

Please ensure that:
1. Each test case is converted to a separate assert statement.
2. The function name in the original example (e.g., 'has_close_elements') is replaced with 'candidate'.
3. The assert statements are returned as strings in a list.
"""
