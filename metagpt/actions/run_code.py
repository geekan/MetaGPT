#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 22:12
@Author  : alexanderwu
@File    : environment.py
"""
import asyncio
from typing import Iterable

from pydantic import BaseModel, Field

from metagpt.memory import Memory
from metagpt.roles import Role
from metagpt.schema import Message


class Environment(BaseModel):
    """Environment that carries a set of roles. Roles can publish messages to the environment, which can be observed by other roles."""

    @classmethod
    async def run_text(cls, code) -> Tuple[str, str]:
        try:
            # We will document_store the result in this dictionary
            namespace = {}
            exec(code, namespace)
            return namespace.get('result', ""), ""
        except Exception:
            # If there is an error in the code, return the error message
            return "", traceback.format_exc()

    @classmethod
    async def run_script(cls, working_directory, additional_python_paths=[], command=[]) -> Tuple[str, str]:
        working_directory = str(working_directory)
        additional_python_paths = [str(path) for path in additional_python_paths]
                # Copy the current environment variables
        env = os.environ.copy()

        # Modify the PYTHONPATH environment variable
        additional_python_paths = [working_directory] + additional_python_paths
        additional_python_paths = ":".join(additional_python_paths)
        env['PYTHONPATH'] = additional_python_paths + ':' + env.get('PYTHONPATH', '')

        # Start the subprocess
        process = subprocess.Popen(command, cwd=working_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

        try:
            # Wait for the process to complete, with a timeout
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            logger.info("The command did not complete within the given timeout.")
            process.kill()  # Kill the process if it times out
            stdout, stderr = process.communicate()
        return stdout.decode('utf-8'), stderr.decode('utf-8')

    async def run(
        self, code, mode="script", code_file_name="", test_code="", test_file_name="", command=[], **kwargs
    ) -> str:
        logger.info(f"Running {' '.join(command)}")
        if mode == "script":
            outs, errs = await self.run_script(command=command, **kwargs)
        elif mode == "text":
            outs, errs = await self.run_text(code=code)

        logger.info(f"{outs=}")
        logger.info(f"{errs=}")

        context = CONTEXT.format(
            code=code, code_file_name=code_file_name,
            test_code=test_code, test_file_name=test_file_name,
            command=" ".join(command),
            outs=outs[:500], # outs might be long but they are not important, truncate them to avoid token overflow
            errs=errs[:10000] # truncate errors to avoid token overflow
        )

        prompt = PROMPT_TEMPLATE.format(context=context)
        rsp = await self._aask(prompt)

        result = context + rsp

        return result
