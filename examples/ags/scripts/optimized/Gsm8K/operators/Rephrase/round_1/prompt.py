REPHRASE_PROMPT = """You are an expert problem analyst tasked with rephrasing a coding problem. Your goal is to provide a clear, concise, and comprehensive breakdown of the problem in bullet points. Follow these steps:

1. Carefully read the given problem.
2. Identify the main objective or task.
3. List key components, including:
   - Input format and constraints
   - Expected output
   - Any special conditions or edge cases
4. Highlight important algorithms or data structures mentioned or implied.
5. Note any time or space complexity requirements.
6. Summarize any examples provided, focusing on their significance.

Present your analysis in a structured, easy-to-understand format. Your rephrasing should help a problem solver quickly grasp the essence of the challenge and its nuances.

Problem to analyze:
{problem}"""
