import json
import os

from pydantic import Field

from metagpt.logs import logger
from metagpt.prompts.di.swe import (
    MINIMAL_EXAMPLE,
    NEXT_STEP_TEMPLATE,
    SWE_AGENT_SYSTEM_TEMPLATE,
)
from metagpt.roles.di.role_zero import RoleZero
from metagpt.tools.libs.terminal import Bash
from metagpt.tools.swe_agent_commands.swe_agent_utils import extract_patch


class SWE(RoleZero):
    name: str = "SweAgent"
    profile: str = "Software Engineer"
    goal: str = "Resolve GitHub issue"
    _bash_window_size: int = 100
    _system_msg: str = SWE_AGENT_SYSTEM_TEMPLATE
    system_msg: list[str] = [_system_msg.format(WINDOW=_bash_window_size)]
    _instruction: str = NEXT_STEP_TEMPLATE
    tools: list[str] = ["Bash", "Browser:goto,scroll"]
    terminal: Bash = Field(default_factory=Bash, exclude=True)
    output_diff: str = ""
    max_react_loop: int = 30

    async def _think(self) -> bool:
        self._set_system_msg()
        self._format_instruction()
        res = await super()._think()
        await self._handle_action()
        return res

    def _set_system_msg(self):
        """
        Sets the system message for the SWE agent.

        Sets the `_bash_window_size` from the environment variable `WINDOW` if it exists.
        Formats the `_system_msg` template with the current `_bash_window_size`.
        """
        if os.getenv("WINDOW"):
            self._bash_window_size = int(os.getenv("WINDOW"))
        self.system_msg = [self._system_msg.format(WINDOW=self._bash_window_size)]

    def _format_instruction(self):
        """
        Formats the instruction message for the SWE agent.

        Runs the "state" command in the terminal, parses its output as JSON,
        and uses it to format the `_instruction` template.
        """
        state_output = self.terminal.run("state")
        bash_state = json.loads(state_output)

        self.instruction = self._instruction.format(
            WINDOW=self._bash_window_size, examples=MINIMAL_EXAMPLE, **bash_state
        ).strip()

        return self.instruction

    async def _handle_action(self):
        """
        Handles actions based on parsed commands.

        Parses commands, checks for a "submit" action, and generates a patch using `git diff`.
        Stores the cleaned patch in `output_diff`. Logs any exceptions.

        This function is specifically added for SWE bench evaluation.
        """
        commands, ok = await self._parse_commands()
        if not ok:
            return
        for cmd in commands:
            if "end" != cmd.get("command_name", ""):
                return
        try:
            diff_output = self.terminal.run("git diff --cached")
            clear_diff = extract_patch(diff_output)
            logger.info(f"Diff output: \n{clear_diff}")
            if clear_diff:
                self.output_diff = clear_diff

        except Exception as e:
            logger.error(f"Error during submission: {e}")

    def _update_tool_execution(self):
        self.tool_execution_map.update({"Bash.run": self.terminal.run})

    def _retrieve_experience(self) -> str:
        return MINIMAL_EXAMPLE
