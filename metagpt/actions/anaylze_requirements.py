import json

from metagpt.actions import Action
from metagpt.utils.common import CodeParser

ANALYZE_REQUIREMENTS = """
# Example 1
Requirements : Create 2048 game. Do not write PRD.
Outputs:{{
    "response_language": "English"
    "requirements_constraints": "Do not write PRD."
}}
# Example 2
Requirements : 创建一个贪吃蛇，只需要给出设计文档和代码
Outputs:{{
    "response_language": "Chinese"
    "requirements_constraints": "只需要给出设计文档和代码"
}}

# Example 3
Requirements :You must ignore create PRD and TRD. Snake Game RequirementsGame InterfaceThe game interface is a rectangular grid.The size of the grid can be adjusted as needed (e.g., 20x20).The snake and the food are displayed on the grid.Game ObjectsSnake: Composed of multiple cells, with an initial length of 3 cells.Food: Appears randomly in one cell on the grid.GameplayThe player controls the snake's movement direction using the arrow keys (up, down, left, right).Each key press changes the snake's movement direction.With each move, the snake's head enters the next cell, and the tail leaves the last cell.When the snake's head meets the food, the snake lengthens by one cell, and new food appears at a random position on the grid.The game ends if the snake's head hits the wall or itself.User InterfaceDisplay the current score (number of food eaten).Display the game status (ongoing or ended).Provide an option to restart the game.Technical RequirementsImplement using HTML, CSS, and JavaScript.Use the Canvas element to draw the game interface.Code should be well-structured and easy to maintain and extend.
Outputs:{{
    "response_language": "English"
    "requirements_constraints": "You must ignore create PRD and TRD."
}}

# Requirements
{requirements}

# Instructions
You must output in the same language as the Requirements.
First, This language should be consistent with the language used in the requirement description. determine the natural language you must respond in. The default language is English
Second, extract the restrictions in the requirements, specifically the steps. Do not include detailed demand descriptions; focus only on the restrictions.

Note:
1. if there is not restrictions, requirements_restrictions must be ""

# Output Format
{{
    "response_language": "the language to respond in"
    "requirements_restrictions": "the restrictions in the requirements"
}}
"""


class AnalyzeRequirementsRestrictions(Action):
    """Write a review for the given context."""

    name: str = "AnalyzeRequirementsRestrictions"

    async def run(self, requirements):
        """Analyze the constraints and the language used in the requirements."""
        node = await self.llm.aask(ANALYZE_REQUIREMENTS.format(requirements=requirements))
        node = CodeParser.parse_code(block=None, lang="json", text=node)
        try:
            node = json.loads(node)
        except:
            node = {}
        # constraints = node.instruct_content.model_dump().get("CONSTRAINTS",None)
        # output_language = node.instruct_content.model_dump().get("OUTPUT_LANGUAGE","English")
        output_language = node.get("response_language", "English")
        constraints = node.get("requirements_restrictions", "")
        format_instruction = ""
        format_instruction += f"1.[User Restrictions] : {constraints}\n"
        format_instruction += (
            f"2.[Language Restrictions] : The response must be in the language specified by {output_language}."
        )
        return format_instruction
