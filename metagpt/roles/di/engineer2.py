from __future__ import annotations

from metagpt.actions.write_code_review import ReviewAndRewriteCode
from metagpt.prompts.di.engineer2 import ENGINEER2_INSTRUCTION
from metagpt.roles.di.role_zero import RoleZero


class Engineer2(RoleZero):
    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = "Take on game, app, and web development"
    instruction: str = ENGINEER2_INSTRUCTION

    tools: str = ["Plan", "Editor:write,read", "RoleZero", "ReviewAndRewriteCode"]

    def _update_tool_execution(self):
        review = ReviewAndRewriteCode()

        self.tool_execution_map.update(
            {
                "ReviewAndRewriteCode.run": review.run,
                "ReviewAndRewriteCode": review.run,
            }
        )
