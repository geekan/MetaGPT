#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : run_code.py
@Modified By: mashenquan, 2023/11/27.
            1. Mark the location of Console logs in the PROMPT_TEMPLATE with markdown code-block formatting to enhance
            the understanding for the LLM.
            2. Fix bug: Add the "install dependency" operation.
            3. Encapsulate the input of RunCode into RunCodeContext and encapsulate the output of RunCode into
            RunCodeResult to standardize and unify parameter passing between WriteCode, RunCode, and DebugError.
            4. According to section 2.2.3.5.7 of RFC 135, change the method of transferring file content
            (code files, unit test files, log files) from using the message to using the file name.
            5. Merged the `Config` class of send18:dev branch to take over the set/get operations of the Environment
            class.
"""
import subprocess
from pathlib import Path
from typing import Tuple

from pydantic import Field

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.schema import RunCodeContext, RunCodeResult
from metagpt.utils.exceptions import handle_exception

PROMPT_TEMPLATE = """
Role: You are a senior development and qa engineer, your role is summarize the code running result.
If the running result does not include an error, you should explicitly approve the result.
On the other hand, if the running result indicates some error, you should point out which part, the development code or the test code, produces the error,
and give specific instructions on fixing the errors. Here is the code info:
{context}
Now you should begin your analysis
---
## instruction:
Please summarize the cause of the errors and give correction instruction
## File To Rewrite:
Determine the ONE file to rewrite in order to fix the error, for example, xyz.py, or test_xyz.py
## Status:
Determine if all of the code works fine, if so write PASS, else FAIL,
WRITE ONLY ONE WORD, PASS OR FAIL, IN THIS SECTION
## Send To:
Please write NoOne if there are no errors, Engineer if the errors are due to problematic development codes, else QaEngineer,
WRITE ONLY ONE WORD, NoOne OR Engineer OR QaEngineer, IN THIS SECTION.
---
You should fill in necessary instruction, status, send to, and finally return all content between the --- segment line.
"""

TEMPLATE_CONTEXT = """
## Development Code File Name
{code_file_name}
## Development Code
```python
{code}
```
## Test File Name
{test_file_name}
## Test Code
```python
{test_code}
```
## Running Command
{command}
## Running Output
standard output: 
```text
{outs}
```
standard errors: 
```text
{errs}
```
"""


class RunCode(Action):
    name: str = "RunCode"
    i_context: RunCodeContext = Field(default_factory=RunCodeContext)

    @classmethod
    async def run_text(cls, code) -> Tuple[str, str]:
        try:
            # We will document_store the result in this dictionary
            namespace = {}
            exec(code, namespace)
        except Exception as e:
            return "", str(e)
        return namespace.get("result", ""), ""

    async def run_script(self, working_directory, additional_python_paths=[], command=[]) -> Tuple[str, str]:
        working_directory = str(working_directory)
        additional_python_paths = [str(path) for path in additional_python_paths]

        # Copy the current environment variables
        env = self.context.new_environ()

        # Modify the PYTHONPATH environment variable
        additional_python_paths = [working_directory] + additional_python_paths
        additional_python_paths = ":".join(additional_python_paths)
        env["PYTHONPATH"] = additional_python_paths + ":" + env.get("PYTHONPATH", "")
        RunCode._install_dependencies(working_directory=working_directory, env=env)

        # Start the subprocess
        process = subprocess.Popen(
            command, cwd=working_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        logger.info(" ".join(command))

        try:
            # Wait for the process to complete, with a timeout
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            logger.info("The command did not complete within the given timeout.")
            process.kill()  # Kill the process if it times out
            stdout, stderr = process.communicate()
        return stdout.decode("utf-8"), stderr.decode("utf-8")

    async def run(self, *args, **kwargs) -> RunCodeResult:
        logger.info(f"Running {' '.join(self.i_context.command)}")
        if self.i_context.mode == "script":
            outs, errs = await self.run_script(
                command=self.i_context.command,
                working_directory=self.i_context.working_directory,
                additional_python_paths=self.i_context.additional_python_paths,
            )
        elif self.i_context.mode == "text":
            outs, errs = await self.run_text(code=self.i_context.code)

        logger.info(f"{outs=}")
        logger.info(f"{errs=}")

        context = TEMPLATE_CONTEXT.format(
            code=self.i_context.code,
            code_file_name=self.i_context.code_filename,
            test_code=self.i_context.test_code,
            test_file_name=self.i_context.test_filename,
            command=" ".join(self.i_context.command),
            outs=outs[:500],  # outs might be long but they are not important, truncate them to avoid token overflow
            errs=errs[:10000],  # truncate errors to avoid token overflow
        )

        prompt = PROMPT_TEMPLATE.format(context=context)
        rsp = await self._aask(prompt)
        return RunCodeResult(summary=rsp, stdout=outs, stderr=errs)

    @staticmethod
    @handle_exception(exception_type=subprocess.CalledProcessError)
    def _install_via_subprocess(cmd, check, cwd, env):
        return subprocess.run(cmd, check=check, cwd=cwd, env=env)

    @staticmethod
    def _install_requirements(working_directory, env):
        file_path = Path(working_directory) / "requirements.txt"
        if not file_path.exists():
            return
        if file_path.stat().st_size == 0:
            return
        install_command = ["python", "-m", "pip", "install", "-r", "requirements.txt"]
        logger.info(" ".join(install_command))
        RunCode._install_via_subprocess(install_command, check=True, cwd=working_directory, env=env)

    @staticmethod
    def _install_pytest(working_directory, env):
        install_pytest_command = ["python", "-m", "pip", "install", "pytest"]
        logger.info(" ".join(install_pytest_command))
        RunCode._install_via_subprocess(install_pytest_command, check=True, cwd=working_directory, env=env)

    @staticmethod
    def _install_dependencies(working_directory, env):
        RunCode._install_requirements(working_directory, env)
        RunCode._install_pytest(working_directory, env)
