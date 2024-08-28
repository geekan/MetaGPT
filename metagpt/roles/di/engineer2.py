from __future__ import annotations

from pydantic import Field

# from metagpt.actions.write_code_review import ValidateAndRewriteCode
from metagpt.prompts.di.engineer2 import (
    ENGINEER2_INSTRUCTION,
    WRITE_CODE_PROMPT,
    WRITE_CODE_SYSTEM_PROMPT,
)
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import UserMessage
from metagpt.strategy.experience_retriever import ENGINEER_EXAMPLE
from metagpt.tools.libs.terminal import Terminal
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import CodeParser, awrite


@register_tool(include_functions=["write_new_code"])
class Engineer2(RoleZero):
    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = "Take on game, app, and web development."
    instruction: str = ENGINEER2_INSTRUCTION

    terminal: Terminal = Field(default_factory=Terminal, exclude=True)

    tools: list[str] = ["Plan", "Editor:read", "RoleZero", "Terminal:run_command", "Engineer2"]

    def _update_tool_execution(self):
        # validate = ValidateAndRewriteCode()
        self.tool_execution_map.update(
            {
                "Terminal.run_command": self.terminal.run_command,
                "Engineer2.write_new_code": self.write_new_code,
                # "ValidateAndRewriteCode.run": validate.run,
                # "ValidateAndRewriteCode": validate.run,
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

    async def write_new_code(self, path: str, instruction: str = "") -> str:
        """Write a new code file.

        Args:
            path (str): The absolute path of the file to be created.
            instruction (optional, str): Further hints or notice other than the current task instruction, must be very concise and can be empty. Defaults to "".
        """
        plan_status, _ = self._get_plan_status()
        prompt = WRITE_CODE_PROMPT.format(
            user_requirement=self.planner.plan.goal,
            plan_status=plan_status,
            instruction=instruction,
        )
        context = self.llm.format_msg(self.rc.memory.get(self.memory_k) + [UserMessage(content=prompt)])
        rsp = await self.llm.aask(context, system_msgs=[WRITE_CODE_SYSTEM_PROMPT])
        code = CodeParser.parse_code(text=rsp)

        await awrite(path, code)

        # TODO: Consider adding line no to be ready for editing.
        return f"The file {path} has been successfully created, with content:\n{code}"
