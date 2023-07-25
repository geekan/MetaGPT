#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : run_code.py
"""
import traceback
import os
import subprocess

from metagpt.logs import logger
from metagpt.actions.action import Action


class RunCode(Action):
    def __init__(self, name="RunCode", context=None, llm=None):
        super().__init__(name, context, llm)

    @classmethod
    async def run_text(cls, code):
        try:
            # We will document_store the result in this dictionary
            namespace = {}
            exec(code, namespace)
            return namespace.get('result', None), ""
        except Exception:
            # If there is an error in the code, return the error message
            return "", traceback.format_exc()

    @classmethod
    async def run_script(cls, working_directory, additional_python_paths=[], command=[]):
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

    async def run(self, context="", mode="script", **kwargs):
        if mode == "script":
            outs, errs = await self.run_script(**kwargs)
        elif mode == "text":
            outs, errs = await self.run_text(**kwargs)
        
        return outs, errs