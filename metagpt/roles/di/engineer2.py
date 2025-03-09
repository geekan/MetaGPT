from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field

from metagpt.logs import logger

# from metagpt.actions.write_code_review import ValidateAndRewriteCode
from metagpt.prompts.di.engineer2 import (
    CURRENT_STATE,
    ENGINEER2_INSTRUCTION,
    WRITE_CODE_PROMPT,
    WRITE_CODE_SYSTEM_PROMPT,
)
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import UserMessage
from metagpt.strategy.experience_retriever import ENGINEER_EXAMPLE
from metagpt.tools.libs.cr import CodeReview
from metagpt.tools.libs.deployer import Deployer
from metagpt.tools.libs.git import git_create_pull
from metagpt.tools.libs.image_getter import ImageGetter
from metagpt.tools.libs.terminal import Terminal
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import CodeParser, awrite
from metagpt.utils.report import EditorReporter


@register_tool(include_functions=["write_new_code"])
class Engineer2(RoleZero):
    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = "Take on game, app, web development and deployment."
    instruction: str = ENGINEER2_INSTRUCTION
    terminal: Terminal = Field(default_factory=Terminal, exclude=True)
    deployer: Deployer = Field(default_factory=Deployer, exclude=True)
    tools: list[str] = [
        "Plan",
        "Editor",
        "RoleZero",
        "Terminal:run_command",
        "Browser:goto,scroll",
        "git_create_pull",
        "SearchEnhancedQA",
        "Engineer2",
        "CodeReview",
        "ImageGetter",
        "Deployer",
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
        Display the current terminal and editor state.
        This information will be dynamically added to the command prompt.
        """
        current_directory = (await self.terminal.run_command("pwd")).strip()
        self.editor._set_workdir(current_directory)
        state = {
            "editor_open_file": self.editor.current_file,
            "current_directory": current_directory,
        }
        self.cmd_prompt_current_state = CURRENT_STATE.format(**state).strip()

    def _update_tool_execution(self):
        # validate = ValidateAndRewriteCode()
        cr = CodeReview()
        image_getter = ImageGetter()
        self.exclusive_tool_commands.append("Engineer2.write_new_code")
        if self.run_eval is True:
            # Evalute tool map
            self.tool_execution_map.update(
                {
                    "git_create_pull": git_create_pull,
                    "Engineer2.write_new_code": self.write_new_code,
                    "ImageGetter.get_image": image_getter.get_image,
                    "CodeReview.review": cr.review,
                    "CodeReview.fix": cr.fix,
                    "Terminal.run_command": self._eval_terminal_run,
                    "RoleZero.ask_human": self._end,
                    "RoleZero.reply_to_human": self._end,
                    "Deployer.deploy_to_public": self._deploy_to_public,
                }
            )
        else:
            # Default tool map
            self.tool_execution_map.update(
                {
                    "git_create_pull": git_create_pull,
                    "Engineer2.write_new_code": self.write_new_code,
                    "ImageGetter.get_image": image_getter.get_image,
                    "CodeReview.review": cr.review,
                    "CodeReview.fix": cr.fix,
                    "Terminal.run_command": self.terminal.run_command,
                    "Deployer.deploy_to_public": self._deploy_to_public,
                }
            )

    def _retrieve_experience(self) -> str:
        return ENGINEER_EXAMPLE

    async def write_new_code(self, path: str, file_description: str = "") -> str:
        """Write a new code file.

        Args:
            path (str): The absolute path of the file to be created.
            file_description (optional, str): "Brief description and important notes of the file content, must be very concise and can be empty. Defaults to "".
        """
        # If the path is not absolute, try to fix it with the editor's working directory.
        path = self.editor._try_fix_path(path)
        plan_status, _ = self._get_plan_status()
        prompt = WRITE_CODE_PROMPT.format(
            user_requirement=self.planner.plan.goal,
            plan_status=plan_status,
            file_path=path,
            file_description=file_description,
            file_name=os.path.basename(path),
        )
        # Sometimes the Engineer repeats the last command to respond.
        # Replace the last command with a manual prompt to guide the Engineer to write new code.
        memory = self.rc.memory.get(self.memory_k)[:-1]
        context = self.llm.format_msg(memory + [UserMessage(content=prompt)])

        async with EditorReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "code", "filename": Path(path).name, "src_path": path}, "meta")
            rsp = await self.llm.aask(context, system_msgs=[WRITE_CODE_SYSTEM_PROMPT])
            code = CodeParser.parse_code(text=rsp)
            await awrite(path, code)
            await reporter.async_report(path, "path")

        # TODO: Consider adding line no to be ready for editing.
        return f"The file {path} has been successfully created, with content:\n{code}"

    async def _deploy_to_public(self, dist_dir):
        """fix the dist_dir path to absolute path before deploying
        Args:
            dist_dir (str): The dist directory of the web project after run build. This must be an absolute path.
        """
        # Try to fix the path with the editor's working directory.
        if not Path(dist_dir).is_absolute():
            default_dir = self.editor._try_fix_path(dist_dir)
            if not default_dir.exists():
                raise ValueError("dist_dir must be an absolute path.")
            dist_dir = default_dir
        return await self.deployer.deploy_to_public(dist_dir)

    async def _eval_terminal_run(self, cmd):
        """change command pull/push/commit to end."""
        if any([cmd_key_word in cmd for cmd_key_word in ["pull", "push", "commit"]]):
            # The Engineer2 attempts to submit the repository after fixing the bug, thereby reaching the end of the fixing process.
            logger.info("Engineer2 use cmd:{cmd}\nCurrent test case is finished.")
            # Set self.rc.todo to None to stop the engineer.
            self._set_state(-1)
        else:
            command_output = await self.terminal.run_command(cmd)
        return command_output

    async def _end(self):
        if not self.planner.plan.is_plan_finished():
            self.planner.plan.finish_all_tasks()
        return await super()._end()
