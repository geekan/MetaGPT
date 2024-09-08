GENERATE_PROMPT = """
Generate Solution for the following problem: 
{problem}

"""

FORMAT_PROMPT = """
For the question described as {problem},
please extract a short and concise answer contains only one word/few words from the following solution: {solution}.
Make sure there are no additional comments or explanations in your response.
"""


CONTEXTUAL_GENERATE_PROMPT = """
Generate Solution for the following problem: 

## Problem Description
{problem}

## Thought
{context}
"""

REVIEW_PROMPT = """
For the question described as {problem},
please review the following solution: {solution}, and provide a review result in boolean format.
If you believe the solution is capable of resolving the issue, return True; otherwise, return False, and include your comments.
"""

REVISE_PROMPT = """
For the question described as {problem},
please evaluate and revise the solution provided: {solution}, taking into account the review feedbacks: {feedback}."
Then output the revised solution.
"""

FU_ENSEMBLE_PROMPT = """
### Given problem

{problem}

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
You are given a problem:
{problem}

Here is a list of possible solutions to the problem:
{solutions}

Using the inputs above, your goal is to choose the best solution to the code contest problem.
Don't just pick the most efficient solution. The main consideration is that the solution can fully solve the problem in a correct and robust manner.
Provide your final decision by writing the chosen solution letter.
"""

SC_ENSEMBLE_PROMPT = """
I have generated the following solutions to the question: {problem}

{solutions}

Evaluate these solutions.
Select the most consistent solution based on majority consensus.
Give your answer with a single id of solution (without anything else).
"""

REPHRASE_PROMPT = """
You are given a code contest problem:

### problem
{problem}

### instrcutions
Given the problem, Your Goal is:
Reflect on the problem, and describe it in your own words, in bullet points. Pay attention to small details, nuances, notes and examples in the problem description.
"""
