from __future__ import annotations

from pydantic import Field

from metagpt.actions.write_code_review import ValidateAndRewriteCode
from metagpt.prompts.di.engineer2 import ENGINEER2_INSTRUCTION
from metagpt.roles.di.role_zero import RoleZero
from metagpt.strategy.experience_retriever import ENGINEER_EXAMPLE
from metagpt.tools.libs.terminal import Terminal


class Engineer2(RoleZero):
    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = "Take on game, app, and web development."
    instruction: str = ENGINEER2_INSTRUCTION

    terminal: Terminal = Field(default_factory=Terminal, exclude=True)

    tools: list[str] = ["Plan", "Editor:write,read", "RoleZero", "Terminal:run_command", "ValidateAndRewriteCode"]

    def _update_tool_execution(self):
        validate = ValidateAndRewriteCode()

        self.tool_execution_map.update(
            {
                "Terminal.run_command": self.terminal.run_command,
                "ValidateAndRewriteCode.run": validate.run,
                "ValidateAndRewriteCode": validate.run,
            }
        )

    def _retrieve_experience(self) -> str:
        return ENGINEER_EXAMPLE

    async def _run_special_command(self, cmd) -> str:
        """command requiring special check or parsing."""
        # finish current task before end.
        command_output = ""
        if cmd["command_name"] == "end" and not self.planner.plan.is_plan_finished():
            self.planner.plan.finish_all_tasks()
            command_output += "All tasks are finished.\n"
        command_output += await super()._run_special_command(cmd)
        return command_output
