REVISE_PROMPT = """Given the problem: {problem}

Initial solution: {solution}

Review feedback: {feedback}

Please revise the solution following these steps:

1. Analyze Feedback:
   - List key issues identified in the feedback
   - Prioritize issues based on their impact on solution accuracy

2. Systematic Revision:
   For each issue, in order of priority:
   a. Explain the specific problem in the original solution
   b. Propose a detailed correction or improvement
   c. Implement the change, showing your work clearly

3. Retain Correct Elements:
   - Identify and preserve accurate parts of the original solution

4. Comprehensive Review:
   - Ensure all aspects of the original problem are addressed
   - Check for consistency and logical flow in the revised solution

5. Enhancement:
   - Suggest any additional improvements for clarity or efficiency
   - Explain the reasoning behind these enhancements

6. Final Solution:
   - Present the fully revised solution
   - Highlight all changes and improvements made

7. Revision Summary:
   - Provide a concise overview of major changes
   - Explain how the revisions address the original feedback

Output the revised solution, emphasizing clarity, accuracy, and completeness."""
