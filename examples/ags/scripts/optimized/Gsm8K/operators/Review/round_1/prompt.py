REVIEW_PROMPT = """You are a meticulous mathematics reviewer. For the problem described as {problem}, carefully analyze the following solution: {solution}. Conduct a thorough review by following these steps:

1. Understand the problem and its requirements.
2. Check if all steps in the solution are mathematically correct.
3. Verify if the solution addresses all parts of the problem.
4. Assess the clarity and logical flow of the solution.
5. Determine if the final answer (if applicable) is correct and properly stated.

After your analysis, provide a review result as follows:
- If the solution correctly and completely solves the problem, return "True".
- If there are any errors, omissions, or unclear explanations, return "False".

Include a brief explanation of your decision, highlighting strengths or areas for improvement. Your review should help improve the solution quality."""
