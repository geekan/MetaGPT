from metagpt.actions import Action

ANALYZE_REQUIREMENTS = """
# Example
{examples}

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
Create 2048 game. Do not write PRD.
Outputs:
[User Restrictions] : Do not write PRD.
[Language Restrictions] : The response must be in the language specified by English.

Example 2
Requirements: 
创建一个贪吃蛇，只需要给出设计文档和代码
Outputs:
[User Restrictions] : 只需要给出设计文档和代码.
[Language Restrictions] : The response must be in the language specified by Chinese.

Example 3
Requirements:
You must ignore create PRD and TRD. Help me write a schedule display program for the Paris Olympics. 
Outputs:
[User Restrictions] : You must ignore create PRD and TRD.
[Language Restrictions] : The response must be in the language specified by English.
"""

INSTRUCTIONS = """
You must output in the same language as the Requirements.
First, This language should be consistent with the language used in the requirement description. determine the natural language you must respond in. The default language is English
Second, extract the restrictions in the requirements, specifically the steps. Do not include detailed demand descriptions; focus only on the restrictions.

Note:
1. if there is not restrictions, requirements_restrictions must be ""
"""

OUTPUT_FORMAT = """
[User Restrictions] : the restrictions in the requirements
[Language Restrictions] :  The response must be in the language specified by {{language}}
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
