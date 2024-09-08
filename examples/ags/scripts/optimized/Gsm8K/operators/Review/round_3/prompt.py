REVIEW_PROMPT = """As a precise mathematics reviewer, evaluate the solution for the problem: {problem}

Solution to review: {solution}

Conduct a thorough review following these steps:
1. Problem Understanding: Ensure all problem components are addressed.
2. Mathematical Accuracy: Verify each step's correctness.
3. Completeness: Check if all required parts are solved.
4. Logical Flow: Assess the solution's structure and clarity.
5. Final Answer: Confirm accuracy and proper presentation.

Provide a structured review:
1. Overall Assessment: "True" if correct and complete, "False" otherwise.
2. Strengths: List up to 3 strong points.
3. Areas for Improvement: Identify up to 3 aspects needing refinement.
4. Specific Feedback: Offer concise, actionable suggestions for enhancement.

Your review should guide towards an improved solution while maintaining brevity and clarity."""
