CONTEXTUAL_GENERATE_PROMPT = """Generate a detailed, context-integrated solution for the given problem:

## Problem
{problem}

## Context
{context}

Follow this enhanced approach:
1. Context Integration:
   - Analyze how the context relates to the problem
   - Identify key insights from the context that can guide the solution

2. Problem Analysis:
   - Restate the problem, incorporating contextual elements
   - Identify and define all relevant variables and parameters
   - Highlight any assumptions based on the context

3. Solution Strategy:
   - Outline a step-by-step approach, influenced by the context
   - Explain the rationale behind your strategy, referencing the context

4. Detailed Solution:
   - Present each step clearly, showing all calculations
   - Integrate contextual information throughout the solution process
   - Use appropriate mathematical notation and explain any complex concepts
   - Apply relevant formulas, theorems, or principles, linking them to the context

5. Verification and Reflection:
   - Validate your solution against the problem requirements and context
   - Discuss how the context influenced your approach and result
   - Address any limitations or alternative interpretations based on the context

6. Conclusion:
   - Summarize the final answer in the context of the original problem
   - Highlight key insights gained from applying the context to the problem

Ensure your solution is:
- Mathematically rigorous and comprehensive
- Clearly explained, demonstrating deep understanding of both problem and context
- Directly addressing all aspects of the problem while integrating contextual information
- Logically structured and easy to follow"""
