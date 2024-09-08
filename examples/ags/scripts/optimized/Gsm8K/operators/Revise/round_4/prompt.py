REVISE_PROMPT = """Given the problem: {problem}

Initial solution: {solution}

Review feedback: {feedback}

Revise the solution following these steps:

1. Analyze Feedback:
   - List key issues from the feedback
   - Prioritize issues by impact on accuracy

2. Systematic Revision:
   For each issue, in priority order:
   a. Explain the problem in the original solution
   b. Propose a detailed correction
   c. Implement the change, showing work clearly

3. Retain Correct Elements:
   - Identify and keep accurate parts of the original solution

4. Comprehensive Review:
   - Address all aspects of the original problem
   - Ensure consistency and logical flow

5. Enhancement:
   - Suggest improvements for clarity or efficiency
   - Explain reasoning behind enhancements

6. Final Solution:
   - Present the fully revised solution
   - Highlight all changes and improvements

7. Revision Summary:
   - Provide a concise overview of major changes
   - Explain how revisions address the original feedback

Output the revised solution, focusing on clarity, accuracy, and completeness."""
