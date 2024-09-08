CONTEXTUAL_GENERATE_PROMPT = """Generate a detailed solution for the following problem:

## Problem Description
{problem}

## Context
{context}

Provide a step-by-step solution following this structure:
1. Problem Analysis: Restate the problem and identify key information.
2. Context Integration: Explain how the given context relates to the problem.
3. Solution Strategy: Outline the steps needed to solve the problem.
4. Execution:
   a. Show all calculations and reasoning.
   b. Explain any mathematical concepts or formulas used.
   c. Use clear, logical progression in your solution.
5. Verification: Check if the answer is reasonable and meets all requirements.
6. Conclusion: Summarize the final answer and key insights.

Ensure your solution:
- Directly addresses the problem using the provided context
- Is mathematically accurate and thorough
- Explains concepts in a way that demonstrates understanding
- Uses appropriate mathematical notation where necessary"""
