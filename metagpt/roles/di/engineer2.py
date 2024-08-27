from __future__ import annotations

import json

from pydantic import Field

from metagpt.actions.write_code_review import ValidateAndRewriteCode
from metagpt.logs import logger
from metagpt.prompts.di.engineer2 import CURRENT_BASH_STATE, ENGINEER2_INSTRUCTION
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import Message
from metagpt.strategy.experience_retriever import ENGINEER_EXAMPLE
from metagpt.tools.libs.git import git_create_pull
from metagpt.tools.libs.terminal import Bash


class Engineer2(RoleZero):
    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = "Take on game, app, and web development."
    instruction: str = ENGINEER2_INSTRUCTION

    # terminal: Terminal = Field(default_factory=Terminal, exclude=True)
    terminal: Bash = Field(default_factory=Bash, exclude=True)

    tools: list[str] = [
        "Plan",
        "Editor:write,read",
        "RoleZero",
        "ValidateAndRewriteCode",
        "Bash",
        "Browser:goto,scroll",
        "git_create_pull",
    ]
    # SWE Agent parameter
    run_eval: bool = False
    output_diff: str = ""
    max_react_loop: int = 40

    async def _think(self) -> bool:
        await self._format_instruction()
        res = await super()._think()
        return res

    async def _format_instruction(self):
        """
        Formats the instruction message for the SWE agent.
        Runs the "state" command in the terminal, parses its output as JSON,
        and uses it to format the `_instruction` template.
        """
        state_output = await self.terminal.run("state")
        bash_state = json.loads(state_output)
        self.cmd_prompt_current_state = CURRENT_BASH_STATE.format(**bash_state).strip()

    def _update_tool_execution(self):
        validate = ValidateAndRewriteCode()
        self.tool_execution_map.update(
            {
                "ValidateAndRewriteCode.run": validate.run,
                "ValidateAndRewriteCode": validate.run,
                "Bash.run": self.eval_terminal_run if self.run_eval else self.terminal.run,
                "git_create_pull": git_create_pull,
            }
        )

    async def eval_terminal_run(self, cmd):
        """change command pull/push/commit to end."""
        if any([cmd_key_word in cmd for cmd_key_word in ["pull", "push", "commit"]]):
            # The SWEAgent attempts to submit the repository after fixing the bug, thereby reaching the end of the fixing process.
            # Set self.rc.todo to None to stop the engineer and then will trigger _save_git_diff funcion to save difference.
            logger.info("SWEAgent use cmd:{cmd}")
            logger.info("Current test case is finished.")
            # stop the sweagent
            self._set_state(-1)
            command_output = "Current test case is finished."
        else:
            command_output = await self.terminal.run(cmd)
        return command_output

    async def _act(self) -> Message:
        message = await super()._act()
        if self.run_eval:
            await self._save_git_diff()
        return message

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

    async def _save_git_diff(self):
        """
        Handles actions based on parsed commands.

        Parses commands, checks for a "submit" action, and generates a patch using `git diff`.
        Stores the cleaned patch in `output_diff`. Logs any exceptions.

        This function is specifically added for SWE bench evaluation.
        """
        # If todo switches to None, it indicates that this is the final round of reactions, and the Swe-Agent will stop. Use git diff to store any changes made.
        if not self.rc.todo:
            print("finish current task *******************************************************")
            from metagpt.tools.swe_agent_commands.swe_agent_utils import extract_patch

            try:
                logger.info(await self.terminal.run("submit"))
                diff_output = await self.terminal.run("git diff --cached")
                clear_diff = extract_patch(diff_output)
                logger.info(f"Diff output: \n{clear_diff}")
                if clear_diff:
                    self.output_diff = clear_diff
            except Exception as e:
                logger.error(f"Error during submission: {e}")
