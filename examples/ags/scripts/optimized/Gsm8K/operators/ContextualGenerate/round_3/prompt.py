CONTEXTUAL_GENERATE_PROMPT = """Generate a comprehensive, step-by-step solution for the given problem:

## Problem
{problem}

## Context
{context}

Follow this structured approach:
1. Problem Analysis:
   - Restate the problem concisely
   - Identify key information and variables
   - Relate the context to the problem

2. Solution Strategy:
   - Outline the main steps to solve the problem
   - Explain the reasoning behind your approach

3. Detailed Solution:
   - Show all calculations and intermediate steps
   - Explain each step clearly
   - Use appropriate mathematical notation
   - Apply relevant formulas or concepts, explaining them briefly

4. Verification:
   - Check your answer for accuracy
   - Ensure all parts of the problem are addressed
   - Verify that the solution aligns with the given context

5. Conclusion:
   - Summarize the final answer
   - Highlight key insights or implications

Ensure your solution is:
- Mathematically accurate and thorough
- Clearly explained, demonstrating deep understanding
- Directly addressing all aspects of the problem
- Properly integrating the provided context"""
