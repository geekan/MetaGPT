from metagpt.actions import Action

ANALYZE_REQUIREMENTS = """
# Example
{examples}

----------------

# Requirements
{requirements}

# Instructions
{instructions}

# Output Format
{output_format}

Follow the instructions and output format. Do not include any additional content.
"""

EXAMPLES = """
Example 1
Requirements: 
创建一个贪吃蛇，只需要给出设计文档和代码
Outputs:
[User Restrictions] : 只需要给出设计文档和代码.
[Language Restrictions] : The response, message and instruction must be in Chinese.
[Programming Language] : HTML (*.html), CSS (*.css), and JavaScript (*.js)

Example 2
Requirements:
Create 2048 game using Python. Do not write PRD.
Outputs:
[User Restrictions] : Do not write PRD.
[Language Restrictions] : The response, message and instruction must be in English.
[Programming Language] : Python

Example 3
Requirements:
You must ignore create PRD and TRD. Help me write a schedule display program for the Paris Olympics. 
Outputs:
[User Restrictions] : You must ignore create PRD and TRD.
[Language Restrictions] : The response, message and instruction must be in English.
[Programming Language] : HTML (*.html), CSS (*.css), and JavaScript (*.js)
"""

INSTRUCTIONS = """
You must output in the same language as the Requirements.
First, This language should be consistent with the language used in the requirement description. determine the natural language you must respond in. If the requirements specify a special language, follow those instructions. The default language for responses is English.
Second, extract the restrictions in the requirements, specifically the steps. Do not include detailed demand descriptions; focus only on the restrictions.
Third, if the requirements is a software development, extract the program language. If no specific programming language is required, Use HTML (*.html), CSS (*.css), and JavaScript (*.js)

Note:
1. if there is not restrictions, requirements_restrictions must be ""
2. if the requirements is a not software development, programming language must be ""
"""

OUTPUT_FORMAT = """
[User Restrictions] : the restrictions in the requirements
[Language Restrictions] :  The response, message and instruction must be in {{language}}
[Programming Language] : Your program must use ...
"""


class AnalyzeRequirementsRestrictions(Action):
    """Write a review for the given context."""

    name: str = "AnalyzeRequirementsRestrictions"

    async def run(self, requirements, isinstance=INSTRUCTIONS, output_format=OUTPUT_FORMAT):
        """Analyze the constraints and the language used in the requirements."""
        prompt = ANALYZE_REQUIREMENTS.format(
            examples=EXAMPLES, requirements=requirements, instructions=isinstance, output_format=output_format
        )
        rsp = await self.llm.aask(prompt)
        return rsp
