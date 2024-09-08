CONTEXTUAL_GENERATE_PROMPT = """Generate a comprehensive solution for the following problem:

## Problem Description
{problem}

## Context
{context}

Please provide a detailed, step-by-step solution following this structure:
1. Understand the problem: Briefly restate the problem and identify key information.
2. Analyze the context: Explain how the given context relates to the problem.
3. Develop a plan: Outline the steps needed to solve the problem.
4. Execute the plan: Show your work, including all calculations and reasoning.
5. Verify the solution: Check if the answer makes sense and meets all requirements.
6. Conclusion: Summarize the final answer and any important insights.

Ensure your solution is clear, logical, and directly addresses the problem using the provided context."""
