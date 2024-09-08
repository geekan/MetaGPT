REPHRASE_PROMPT = """As an expert problem analyst, your task is to rephrase and analyze the given coding problem. Present a clear, structured breakdown using the following format:

1. Main Objective: [Concise statement of the primary goal]

2. Input:
   - Format: [Describe input structure]
   - Constraints: [List key limitations or ranges]

3. Output:
   - Expected format: [Describe required output]

4. Key Components:
   - [List crucial elements or steps of the problem]

5. Algorithmic Considerations:
   - [Mention relevant algorithms or data structures]
   - Time/Space Complexity: [Note any specified requirements]

6. Special Conditions:
   - [Highlight edge cases or unique scenarios]

7. Example Breakdown:
   - [Brief analysis of provided examples, if any]

Provide this analysis in a concise, bullet-point format to facilitate quick understanding of the problem's essence and critical aspects.

Problem to analyze:
{problem}"""
