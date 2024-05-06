#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Union


async def shell_execute(
    command: Union[List[str], str], cwd: str | Path = None, env: Dict = None, timeout: int = 600
) -> Tuple[str, str, int]:
    """
    Execute a command asynchronously and return its standard output and standard error.

    Args:
        command (Union[List[str], str]): The command to execute and its arguments. It can be provided either as a list
            of strings or as a single string.
        cwd (str | Path, optional): The current working directory for the command. Defaults to None.
        env (Dict, optional): Environment variables to set for the command. Defaults to None.
        timeout (int, optional): Timeout for the command execution in seconds. Defaults to 600.

    Returns:
        Tuple[str, str, int]: A tuple containing the string type standard output and string type standard error of the executed command and int type return code.

    Raises:
        ValueError: If the command times out, this error is raised. The error message contains both standard output and
         standard error of the timed-out process.

    Example:
        >>> # command is a list
        >>> stdout, stderr, returncode = await shell_execute(command=["ls", "-l"], cwd="/home/user", env={"PATH": "/usr/bin"})
        >>> print(stdout)
        total 8
        -rw-r--r-- 1 user user    0 Mar 22 10:00 file1.txt
        -rw-r--r-- 1 user user    0 Mar 22 10:00 file2.txt
        ...

        >>> # command is a string of shell script
        >>> stdout, stderr, returncode = await shell_execute(command="ls -l", cwd="/home/user", env={"PATH": "/usr/bin"})
        >>> print(stdout)
        total 8
        -rw-r--r-- 1 user user    0 Mar 22 10:00 file1.txt
        -rw-r--r-- 1 user user    0 Mar 22 10:00 file2.txt
        ...

    References:
        This function uses `subprocess.Popen` for executing shell commands asynchronously.
    """
    cwd = str(cwd) if cwd else None
    shell = True if isinstance(command, str) else False
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, env=env, timeout=timeout, shell=shell)
    return result.stdout, result.stderr, result.returncode
