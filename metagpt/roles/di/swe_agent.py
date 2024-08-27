import json

from pydantic import Field

from metagpt.logs import logger
from metagpt.prompts.di.swe_agent import (
    CURRENT_BASH_STATE,
    MINIMAL_EXAMPLE,
    NEXT_STEP_TEMPLATE,
)
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import Message
from metagpt.tools.libs.git import git_create_pull
from metagpt.tools.libs.terminal import Bash


class SWEAgent(RoleZero):
    name: str = "Swen"
    profile: str = "Issue Solver"
    goal: str = "Resolve GitHub issue or bug in any existing codebase"
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
        return res

    def _update_tool_execution(self):
        self.tool_execution_map.update(
            {
                "Bash.run": self.eval_terminal_run if self.run_eval else self.terminal.run,
                "git_create_pull": git_create_pull,
            }
        )

    async def eval_terminal_run(self, cmd):
        """change command pull/push/commit to end."""
        if any([cmd_key_word in cmd for cmd_key_word in ["pull", "push", "commit"]]):
            # Observe that SWEAgent tries to submit the repo after fixing the bug.
            # Set self.rc.todo to None and use git -diff to record the change.
            logger.info("SWEAgent use cmd:{cmd}")
            logger.info("finish current task")
            # stop the sweagent
            self._set_state(-1)
            command_output = "Current test case is finished."
        else:
            command_output = await self.terminal.run(cmd)
        return command_output

    async def _format_instruction(self):
        """
        Formats the instruction message for the SWE agent.

        Runs the "state" command in the terminal, parses its output as JSON,
        and uses it to format the `_instruction` template.
        """
        state_output = await self.terminal.run("state")
        bash_state = json.loads(state_output)
        self.cmd_prompt_current_state = CURRENT_BASH_STATE.format(**bash_state).strip()

    async def _act(self) -> Message:
        message = await super()._act()
        if self.run_eval:
            await self._parse_commands_for_eval()
        return message

    async def _parse_commands_for_eval(self):
        """
        Handles actions based on parsed commands.

        Parses commands, checks for a "submit" action, and generates a patch using `git diff`.
        Stores the cleaned patch in `output_diff`. Logs any exceptions.

        This function is specifically added for SWE bench evaluation.
        """
        # If todo switches to None, it indicates that this is the final round of reactions, and the Swe-Agent will stop. Use git diff to store any changes made.
        if not self.rc.todo:
            from metagpt.tools.swe_agent_commands.swe_agent_utils import extract_patch

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
