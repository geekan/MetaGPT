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
