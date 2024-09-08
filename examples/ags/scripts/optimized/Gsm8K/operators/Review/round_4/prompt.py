REVIEW_PROMPT = """As a precise mathematics reviewer, evaluate the solution for the problem: {problem}

Solution to review: {solution}

Follow this structured review process:
1. Problem Understanding: Does the solution demonstrate clear comprehension of the problem?
2. Approach: Is the chosen method appropriate and efficient?
3. Execution: Are calculations accurate and steps logically sequenced?
4. Completeness: Does the solution address all parts of the problem?
5. Presentation: Is the solution clearly explained and well-organized?

For each step, assign a score (0-2):
0 - Unsatisfactory
1 - Partially correct
2 - Excellent

Tally the scores. If the total is 8-10, return "True". Otherwise, return "False".

Provide brief, constructive feedback highlighting strengths and areas for improvement, focusing on the most critical aspects that could enhance the solution's quality."""
