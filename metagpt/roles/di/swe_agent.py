import json
from typing import Optional

from pydantic import Field

from metagpt.logs import logger
from metagpt.prompts.di.swe_agent import (
    MINIMAL_EXAMPLE,
    NEXT_STEP_TEMPLATE,
    SWE_AGENT_SYSTEM_TEMPLATE,
)
from metagpt.roles.di.role_zero import RoleZero
from metagpt.tools.libs.git import git_create_pull
from metagpt.tools.libs.terminal import Bash


class SWEAgent(RoleZero):
    name: str = "Swen"
    profile: str = "Issue Solver"
    goal: str = "Resolve GitHub issue or bug in any existing codebase"
    system_msg: Optional[list[str]] = [SWE_AGENT_SYSTEM_TEMPLATE]
    _instruction: str = NEXT_STEP_TEMPLATE
    tools: list[str] = [
        "Bash",
        "Browser:goto,scroll",
        "RoleZero",
        "git_create_pull",
    ]
    terminal: Bash = Field(default_factory=Bash, exclude=True)
    output_diff: str = ""
    max_react_loop: int = 40
    run_eval: bool = False

    async def _think(self) -> bool:
        await self._format_instruction()
        res = await super()._think()
        if self.run_eval:
            await self._parse_commands_for_eval()
        return res

    def _update_tool_execution(self):
        self.tool_execution_map.update(
            {
                "Bash.run": self.terminal.run,
                "git_create_pull": git_create_pull,
            }
        )

    async def _format_instruction(self):
        """
        Formats the instruction message for the SWE agent.

        Runs the "state" command in the terminal, parses its output as JSON,
        and uses it to format the `_instruction` template.
        """
        state_output = await self.terminal.run("state")
        bash_state = json.loads(state_output)
        self.instruction = self._instruction.format(**bash_state).strip()

    async def _parse_commands_for_eval(self):
        """
        Handles actions based on parsed commands.

        Parses commands, checks for a "submit" action, and generates a patch using `git diff`.
        Stores the cleaned patch in `output_diff`. Logs any exceptions.

        This function is specifically added for SWE bench evaluation.
        """
        # only import when evaluation is needed
        from metagpt.tools.swe_agent_commands.swe_agent_utils import extract_patch

        commands, ok = await self._parse_commands()
        if not ok:
            return
        for cmd in commands:
            if "end" != cmd.get("command_name", ""):
                return
        try:
            diff_output = await self.terminal.run("git diff --cached")
            clear_diff = extract_patch(diff_output)
            logger.info(f"Diff output: \n{clear_diff}")
            if clear_diff:
                self.output_diff = clear_diff

        except Exception as e:
            logger.error(f"Error during submission: {e}")

    def _retrieve_experience(self) -> str:
        return MINIMAL_EXAMPLE
