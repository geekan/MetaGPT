GENERATE_PROMPT = """
Generate Solution for the following problem: {problem_description}
"""

REPHRASE_ON_PROBLEM_PROMPT = """
You are presented with a math contest question:

### Problem
{problem_description}

### Instructions
When faced with this math problem, your goal is to:
1. Read the problem carefully and understand the basic requirements and conditions.
2. Restate the problem in your own words, capturing the nuances, details, notes, and examples provided in the problem description.
3. List the key points for solving the problem, including known conditions, unknowns, and mathematical concepts or formulas that need to be applied.
4. Consider possible strategies and methods for solving the problem, thinking about how to break it down into smaller parts or steps.
5. Attempt to represent the problem with mathematical expressions or equations to prepare for solving it.
"""

ANSWER_FORMAT_PROMPT = """
### Answer
{problem_description}

### Instructions
Provide the answer as a numerical value only, without units or any additional text.
"""