SC_ENSEMBLE_PROMPT = """You are an expert evaluator tasked with selecting the best solution to this problem: {problem}

Analyze the following solutions:
{solutions}

Your evaluation process:
1. Assess each solution for correctness, completeness, and logical consistency.
2. Identify common approaches and unique insights across solutions.
3. Consider edge cases and potential limitations of each solution.
4. Evaluate the clarity and efficiency of each solution's reasoning.
5. Determine which solution(s) most accurately and comprehensively address the problem.
6. If multiple solutions are similar, use a majority consensus approach, but also consider the merits of unique, correct approaches.

Provide your answer as a single integer ID corresponding to the best solution. Do not include any additional text or explanation."""
