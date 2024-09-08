REVISE_PROMPT = """Given the problem: {problem}

And the initial solution: {solution}

Consider the review feedback: {feedback}

Please revise the solution following these steps:
1. Identify the key issues mentioned in the feedback.
2. For each issue:
   a. Explain the problem with the original solution.
   b. Propose a specific correction or improvement.
   c. Implement the change in the solution.
3. If any parts of the original solution are correct and unaffected by the feedback, retain them.
4. Ensure the revised solution addresses all aspects of the original problem.
5. Provide a brief summary of all changes made.

Output the revised solution, highlighting the improvements made based on the feedback."""
