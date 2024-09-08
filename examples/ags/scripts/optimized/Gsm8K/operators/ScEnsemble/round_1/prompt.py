SC_ENSEMBLE_PROMPT = """You are tasked with evaluating multiple solutions to the following problem: {problem}

Here are the generated solutions:
{solutions}

Your task:
1. Carefully analyze each solution for correctness, completeness, and logical consistency.
2. Identify any common patterns or approaches among the solutions.
3. Determine which solution(s) most accurately and comprehensively address the problem.
4. Select the best solution based on your analysis, considering majority consensus if multiple solutions are similar.

Provide your answer as a single ID number corresponding to the best solution, without any additional text or explanation."""
