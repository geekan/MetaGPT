from __future__ import annotations

import asyncio

from pydantic import model_validator

from metagpt.roles.di.role_zero import RoleZero
from metagpt.tools.libs.editor import Editor
from test3 import design_doc_2048, design_doc_snake, task_doc_2048, task_doc_snake


def dummy_func(**kwargs):
    pass


class Engineer2(RoleZero):
    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = ""
    tools: str = ["Plan", "Editor:write,read,write_content", "MGXEnv:ask_human,reply_to_human"]

    editor: Editor = Editor()

    @model_validator(mode="after")
    def set_tool_execution_map(self) -> "RoleZero":
        self.tool_execute_map = {
            "Plan.append_task": self.planner.plan.append_task,
            "Plan.reset_task": self.planner.plan.reset_task,
            "Plan.replace_task": self.planner.plan.replace_task,
            "Editor.write": self.editor.write,
            "Editor.write_content": self.editor.write_content,
            "Editor.read": self.editor.read,
            "MGXEnv.ask_human": dummy_func,
            "MGXEnv.reply_to_human": dummy_func,
        }
        return self


GAME_REQ_2048 = f"""
Create a 2048 game, follow the design doc and task doc. Write your code under /Users/gary/Files/temp/workspace/2048_game/src.
After writing all codes, write a code review for the codes, make improvement or adjustment based on the review.
Notice: You MUST implement the full code, don't leave comment without implementation!
Design doc:
{task_doc_2048}
Task doc:
{design_doc_2048}
"""
GAME_REQ_SNAKE = f"""
Create a snake game, follow the design doc and task doc. Write your code under /Users/gary/Files/temp/workspace/snake_game/src.
After writing all codes, write a code review for the codes, make improvement or adjustment based on the review.
Notice: You MUST implement the full code, don't leave comment without implementation!
Design doc:
{task_doc_snake}
Task doc:
{design_doc_snake}
"""
GAME_REQ_2048_NO_DOC = """
Create a 2048 game with pygame. Write your code under /Users/gary/Files/temp/workspace/2048_game/src.
Consider what files you will write, break down the requests to multiple tasks and write one file in each task.
After writing all codes, write a code review for the codes, make improvement or adjustment based on the review.
Notice: You MUST implement the full code, don't leave comment without implementation!
"""
GAME_INC_REQ_2048 = """
I found an issue with the 2048 code: when tiles are merged, no new tiles pop up.
Write code review for the codes (game.py, main.py, ui.py) under under /Users/gary/Files/temp/workspace/2048_game_bugs/src.
Then correct any issues you find. You can review all code in one time, and solve issues in one time.
"""
GAME_INC_REQ_SNAKE = """
Found this issue, TypeError: generate_new_position() missing 1 required positional argument: 'snake_body'
Write code review for the codes (food.py, game.py, main.py, snake.py, ui.py) under under /Users/gary/Files/temp/workspace/snake_game_bugs/src.
Then correct any issues you find. You can review all code in one time, and solve issues in one time.
"""

if __name__ == "__main__":
    engineer2 = Engineer2()
    asyncio.run(engineer2.run(GAME_REQ_2048_NO_DOC))
