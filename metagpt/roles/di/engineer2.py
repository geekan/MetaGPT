from __future__ import annotations

from pydantic import model_validator

from metagpt.prompts.di.engineer2 import ENGINEER2_INSTRUCTION
from metagpt.roles.di.role_zero import RoleZero
from metagpt.tools.libs.editor import Editor


class Engineer2(RoleZero):
    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = "Take on game, app, and web development"
    instruction: str = ENGINEER2_INSTRUCTION

    tools: str = ["Plan", "Editor:write,read,write_content", "RoleZero"]
    editor: Editor = Editor()

    @model_validator(mode="after")
    def set_tool_execution(self) -> "RoleZero":
        self.tool_execution_map = {
            "Plan.append_task": self.planner.plan.append_task,
            "Plan.reset_task": self.planner.plan.reset_task,
            "Plan.replace_task": self.planner.plan.replace_task,
            "Editor.write": self.editor.write,
            "Editor.write_content": self.editor.write_content,
            "Editor.read": self.editor.read,
            "RoleZero.ask_human": self.ask_human,
            "RoleZero.reply_to_human": self.reply_to_human,
        }
        return self
