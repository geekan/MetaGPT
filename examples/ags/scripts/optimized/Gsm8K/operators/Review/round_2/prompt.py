REVIEW_PROMPT = """As a precise mathematics reviewer, evaluate the solution for the problem: {problem}

Solution to review: {solution}

Follow these steps:
1. Comprehension: Ensure full understanding of the problem.
2. Accuracy: Verify each mathematical step.
3. Completeness: Check if all problem parts are addressed.
4. Clarity: Assess solution's logical flow and explanation.
5. Correctness: Confirm the final answer's accuracy.

Score each criterion from 0-2:
0 = Unsatisfactory
1 = Partially meets expectations
2 = Fully satisfactory

Calculate total score (max 10).

Provide feedback for each criterion.

Return:
- If total score ≥ 8: "True"
- If total score < 8: "False"

Include brief explanation and improvement suggestions.

Your thorough review will enhance solution quality and mathematical understanding."""
