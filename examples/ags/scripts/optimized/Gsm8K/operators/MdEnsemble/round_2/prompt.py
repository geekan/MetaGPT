MD_ENSEMBLE_PROMPT = """As an expert mathematical solution evaluator, your task is to select the optimal solution for the given problem. You will receive:

Problem: {problem}

Candidate Solutions:
{solutions}

Evaluation process:
1. Assess each solution for:
   a) Mathematical accuracy
   b) Problem-solving approach
   c) Clarity and conciseness
   d) Handling of edge cases
2. Assign a score (1-10) to each solution based on the above criteria.
3. Rank the solutions from best to worst.
4. Select the highest-scoring solution as the best.

In your response:
1. Provide the letter of the chosen best solution.
2. Briefly explain your selection, highlighting:
   - Key strengths of the chosen solution
   - Any notable advantages over other solutions
   - Potential improvements or considerations for future problem-solving

Your evaluation should prioritize mathematical correctness and effective problem-solving strategies."""
