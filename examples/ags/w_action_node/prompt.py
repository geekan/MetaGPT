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
You are an expert programmer tasked with solving a coding problem.

### Problem Description:
{problem_description}

### Instructions:
The above is an incomplete Python code fragment. Return the complete and correct code with no additional text.
Please maintain the JSON format in your response.
### Your Response: 

"""
GENERATE_CODEBLOCK_PROMPT = """
You are an expert programmer tasked with solving a coding problem.

### Problem Description:
{problem_description}

### Instructions:
The above is an incomplete Python code fragment. Return the complete and correct code with no additional text.
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
{{
    "reason":"<为什么要这样做>",
    "code_solution":"<你觉得合适的solution，用代码表示出来>"
}}
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

