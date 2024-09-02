from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field

from metagpt.config2 import Config
from metagpt.logs import logger

# from metagpt.actions.write_code_review import ValidateAndRewriteCode
from metagpt.prompts.di.engineer2 import (
    CURRENT_EDITOR_STATE,
    CURRENT_TERMINAL_STATE,
    ENGINEER2_INSTRUCTION,
    WRITE_CODE_PROMPT,
    WRITE_CODE_SYSTEM_PROMPT,
)
from metagpt.prompts.di.role_zero import CMD_PROMPT
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import Message, UserMessage
from metagpt.strategy.experience_retriever import ENGINEER_EXAMPLE
from metagpt.tools.libs.git import git_create_pull
from metagpt.tools.libs.terminal import Terminal
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import CodeParser, awrite
from metagpt.utils.report import EditorReporter


@register_tool(include_functions=["write_new_code"])
class Engineer2(RoleZero):
    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = "Take on game, app, and web development."
    instruction: str = ENGINEER2_INSTRUCTION
    cmd_prompt: str = (
        CMD_PROMPT
        + "\nWhen using the Editor tool, the command list must contain a single command. Because the command is mutually exclusive."
    )
    terminal: Terminal = Field(default_factory=Terminal, exclude=True)

    tools: list[str] = [
        "Plan",
        "Editor",
        "RoleZero",
        "Terminal",
        "Browser:goto,scroll",
        "git_create_pull",
        "Engineer2",
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
        Formats the instruction message for the Engineer2.
        Uses Editor's state to format the `_instruction` template.
        """
        bash_working_dir = await self.terminal.run_command("pwd")
        bash_state = {"working_dir": bash_working_dir}
        editor_state = {"open_file": self.editor.current_file, "working_dir": self.editor.working_dir}
        self.cmd_prompt_current_state = CURRENT_EDITOR_STATE.format(
            **editor_state
        ).strip() + CURRENT_TERMINAL_STATE.format(**bash_state)

    def _update_tool_execution(self):
        self.tool_execution_map.update(
            {
                "Terminal.run_command": self.eval_terminal_run if self.run_eval else self.terminal.run_command,
                "git_create_pull": git_create_pull,
                "Engineer2.write_new_code": self.write_new_code,
                # "ValidateAndRewriteCode.run": validate.run,
                # "ValidateAndRewriteCode": validate.run,
            }
        )

    async def eval_terminal_run(self, cmd):
        """change command pull/push/commit to end."""
        if any([cmd_key_word in cmd for cmd_key_word in ["pull", "push", "commit"]]):
            # The Engineer2 attempts to submit the repository after fixing the bug, thereby reaching the end of the fixing process.
            # Set self.rc.todo to None to stop the engineer and then will trigger _save_git_diff funcion to save difference.
            logger.info("Engineer2 use cmd:{cmd}")
            logger.info("Current test case is finished.")
            # stop the Engineer2
            self._set_state(-1)
            command_output = "Current test case is finished."
        else:
            command_output = await self.terminal.run_command(cmd)
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

        When detecting engineer2 at the final action round, the process will stop immediately.
        generates a patch using `git diff`.
        Stores the cleaned patch in `output_diff`. Logs any exceptions.

        This function is specifically added for SWE bench evaluation.
        """
        # If todo switches to None, it indicates that this is the final round of reactions, and the Engineer2 will stop. Use git diff to store any changes made.
        if not self.rc.todo:
            from metagpt.tools.swe_agent_commands.swe_agent_utils import extract_patch

            try:
                logger.info(await self.submit())
                diff_output = await self.terminal.run_command("git diff --cached")
                clear_diff = extract_patch(diff_output)
                logger.info(f"Diff output: \n{clear_diff}")
                if clear_diff:
                    self.output_diff = clear_diff
            except Exception as e:
                logger.error(f"Error during submission: {e}")

    async def submit(self):
        if "SWE_CMD_WORK_DIR" not in os.environ:
            os.environ["SWE_CMD_WORK_DIR"] = str(Config.default().workspace.path)
        if os.path.exists(os.environ["SWE_CMD_WORK_DIR"] + "/test.patch"):
            await self.terminal.run_command('git apply -R < "$SWE_CMD_WORK_DIR/test.patch"')
        cmd = """
        git add -A
        echo "<<SUBMISSION START||"
        git diff --cached
        echo "||SUBMISSION DONE>>"
        """
        diff_output = await self.terminal.run_command(cmd)
        return diff_output

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

        async with EditorReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "code", "filename": Path(path).name, "src_path": path}, "meta")
            rsp = await self.llm.aask(context, system_msgs=[WRITE_CODE_SYSTEM_PROMPT])
            code = CodeParser.parse_code(text=rsp)
            await awrite(path, code)
            await reporter.async_report(path, "path")

        # TODO: Consider adding line no to be ready for editing.
        return f"The file {path} has been successfully created, with content:\n{code}"
