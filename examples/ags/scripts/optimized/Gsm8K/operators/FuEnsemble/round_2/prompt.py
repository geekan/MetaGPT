FU_ENSEMBLE_PROMPT = """### Given problem
{problem}

### We've got a list of solutions
<solutions>
{solutions}
</solutions>

### Instructions
Analyze the given problem and solution candidates to synthesize an optimal mathematical solution:

1. Evaluation:
   - Assess each solution's mathematical accuracy and logical consistency
   - Identify correct steps, innovative approaches, and potential errors

2. Error Correction:
   - Pinpoint and rectify any mathematical mistakes or logical flaws
   - Ensure all calculations and algebraic manipulations are precise

3. Integration:
   - Combine the most effective and accurate elements from different solutions
   - Create a step-by-step approach that clearly shows the problem-solving process

4. Optimization:
   - Simplify complex steps where possible without losing accuracy
   - Incorporate efficient mathematical techniques or shortcuts if applicable

5. Verification:
   - Rigorously test the integrated solution against the original problem
   - Confirm all variables and conditions in the problem are addressed

6. Presentation:
   - Present the final solution in a clear, logical sequence of steps
   - Include brief explanations for key mathematical decisions or techniques used

Synthesize these elements into a comprehensive, mathematically sound solution that excels in both accuracy and clarity."""
