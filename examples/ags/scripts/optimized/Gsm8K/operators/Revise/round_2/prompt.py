REVISE_PROMPT = """Given the problem: {problem}

Initial solution: {solution}

Review feedback: {feedback}

Revise the solution as follows:

1. Analyze feedback:
   - List key issues identified
   - Prioritize corrections needed

2. For each issue:
   a. Explain the error in the original solution
   b. Outline the necessary correction
   c. Implement the change

3. Retain correct parts of the original solution

4. Verify revised solution:
   - Addresses all aspects of the problem
   - Incorporates all feedback
   - Maintains mathematical accuracy

5. Summarize revisions:
   - List all changes made
   - Explain how each improves the solution

Provide the revised solution, clearly indicating all modifications and improvements based on the feedback."""
