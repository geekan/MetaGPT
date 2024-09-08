FU_ENSEMBLE_PROMPT = """### Given problem
{problem}

### We've got a list of solutions
<solutions>
{solutions}
</solutions>

### Instructions
Analyze the given problem and solution candidates to synthesize an optimal solution:

1. Evaluation:
   - Assess each solution's accuracy, efficiency, and completeness
   - Identify unique strengths and potential weaknesses

2. Integration:
   - Combine the best elements from different solutions
   - Address any gaps or inconsistencies in the proposed approaches

3. Enhancement:
   - Introduce innovative techniques or perspectives if applicable
   - Ensure the final solution is comprehensive and logically sound

4. Verification:
   - Cross-check the integrated solution against the original problem
   - Confirm all aspects of the problem are addressed

5. Presentation:
   - Articulate the final solution clearly and concisely
   - Provide a brief rationale for key decisions in the synthesis process

Synthesize these insights into a cohesive, optimized solution that surpasses the individual candidates in effectiveness and completeness."""


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


SC_ENSEMBLE_PROMPT = """You are an expert evaluator tasked with selecting the best solution to this problem: {problem}

Analyze the following solutions:
{solutions}

Your evaluation process:
1. Assess each solution for correctness, completeness, and logical consistency.
2. Identify common approaches and unique insights across solutions.
3. Consider edge cases and potential limitations of each solution.
4. Evaluate the clarity and efficiency of each solution's reasoning.
5. Determine which solution(s) most accurately and comprehensively address the problem.
6. If multiple solutions are similar, use a majority consensus approach, but also consider the merits of unique, correct approaches.

Provide your answer as a single integer ID corresponding to the best solution. Do not include any additional text or explanation."""


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
