import asyncio
import os
import re
import sys
from asyncio import Queue
from asyncio.subprocess import PIPE, STDOUT
from typing import Optional

from metagpt.config2 import Config
from metagpt.const import DEFAULT_WORKSPACE_ROOT, SWE_SETUP_PATH
from metagpt.logs import logger
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.report import END_MARKER_VALUE, TerminalReporter

DEFAULT_COMMAND_TIMEOUT = 600
TIMEOUT_MESSAGE = (
    "\n[Terminal timeout] The command did not finish within {timeout} seconds and was terminated. "
    "The shell session has been reset, so the working directory and shell variables are back to their defaults. "
    "Run long-running commands with `daemon=True`, or raise the limit via the METAGPT_TERMINAL_TIMEOUT "
    "environment variable.\n"
)


def get_default_command_timeout() -> Optional[float]:
    """Return the per-command timeout in seconds, or None if timeouts are disabled.

    Configurable through the `METAGPT_TERMINAL_TIMEOUT` environment variable; a value of 0
    (or below) disables the timeout.
    """
    raw = os.environ.get("METAGPT_TERMINAL_TIMEOUT")
    if raw is None:
        return DEFAULT_COMMAND_TIMEOUT
    try:
        timeout = float(raw)
    except ValueError:
        logger.warning(f"Invalid METAGPT_TERMINAL_TIMEOUT={raw!r}, falling back to {DEFAULT_COMMAND_TIMEOUT}s.")
        return DEFAULT_COMMAND_TIMEOUT
    return timeout if timeout > 0 else None


@register_tool()
class Terminal:
    """
    A tool for running terminal commands.
    Don't initialize a new instance of this class if one already exists.
    For commands that need to be executed within a Conda environment, it is recommended
    to use the `execute_in_conda_env` method.
    """

    def __init__(self):
        if sys.platform.startswith("win"):
            self.shell_command = ["cmd.exe"]  # Windows
            self.executable = None
            self.command_terminator = "\r\n"
            self.pwd_command = "cd"
        else:
            self.shell_command = ["bash"]  # Linux / macOS
            self.executable = "bash"
            self.command_terminator = "\n"
            self.pwd_command = "pwd"

        self.stdout_queue = Queue(maxsize=1000)
        self.observer = TerminalReporter()
        self.process: Optional[asyncio.subprocess.Process] = None
        # Upper bound for a single non-daemon command. Set to None to wait forever.
        self.command_timeout: Optional[float] = get_default_command_timeout()
        #  The cmd in forbidden_terminal_commands will be replace by pass ana return the advise. example:{"cmd":"forbidden_reason/advice"}
        self.forbidden_commands = {
            "run dev": "Use Deployer.deploy_to_public instead.",
            # serve cmd have a space behind it,
            "serve ": "Use Deployer.deploy_to_public instead.",
        }

    async def _start_process(self):
        # Start a persistent shell process
        self.process = await asyncio.create_subprocess_exec(
            *self.shell_command,
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
            executable=self.executable,
            env=os.environ.copy(),
            cwd=str(DEFAULT_WORKSPACE_ROOT) if sys.platform.startswith("win") else DEFAULT_WORKSPACE_ROOT,  # Windows
        )
        await self._check_state()

    async def _check_state(self):
        """
        Check the state of the terminal, e.g. the current directory.
        """
        output = await self.run_command(self.pwd_command)
        logger.info("The terminal is at:", output)

    async def run_command(self, cmd: str, daemon=False, timeout: Optional[float] = None) -> str:
        """
        Executes a specified command in the terminal and streams the output back in real time.
        This command maintains state across executions, such as the current directory,
        allowing for sequential commands to be contextually aware.

        Args:
            cmd (str): The command to execute in the terminal.
            daemon (bool): If True, executes the command in an asynchronous task, allowing
                           the main program to continue execution.
            timeout (float): Maximum number of seconds to wait for the command to finish.
                             Defaults to `self.command_timeout` (600s, configurable through the
                             `METAGPT_TERMINAL_TIMEOUT` environment variable). On timeout the shell
                             is restarted and the partial output is returned together with an
                             explicit timeout notice. Ignored when `daemon` is True.
        Returns:
            str: The command's output or an empty string if `daemon` is True. Remember that
                 when `daemon` is True, use the `get_stdout_output` method to get the output.
        """
        if self.process is None:
            await self._start_process()

        output = ""
        # Remove forbidden commands
        commands = re.split(r"\s*&&\s*", cmd)
        skip_cmd = "echo Skipped" if sys.platform.startswith("win") else "true"
        for cmd_name, reason in self.forbidden_commands.items():
            # "true" is a pass command in linux terminal.
            for index, command in enumerate(commands):
                if cmd_name in command:
                    output += f"Failed to execute {command}. {reason}\n"
                    commands[index] = skip_cmd
        cmd = " && ".join(commands)
        # Send the command
        self.process.stdin.write((cmd + self.command_terminator).encode())

        marker_cmd = f"echo {END_MARKER_VALUE}"
        self.process.stdin.write((marker_cmd + self.command_terminator).encode())  # Unique marker to signal command end
        await self.process.stdin.drain()

        if daemon:
            asyncio.create_task(self._read_and_process_output(cmd))
        else:
            output += await self._run_until_marker(cmd, self.command_timeout if timeout is None else timeout)

        return output

    async def _run_until_marker(self, cmd: str, timeout: Optional[float]) -> str:
        """Read the output of `cmd` until the end marker, giving up after `timeout` seconds."""
        # `cmd_output` is shared with the reader so partial output survives a timeout.
        cmd_output = []
        reader = self._read_and_process_output(cmd, cmd_output=cmd_output)
        if not timeout:
            return await reader

        try:
            return await asyncio.wait_for(reader, timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Command timed out after {timeout}s, restarting the terminal: {cmd}")
            # The command may still be running and would corrupt the output of the next one,
            # so drop the shell. The next command starts a fresh session.
            await self._terminate_process()
            return "".join(cmd_output) + TIMEOUT_MESSAGE.format(timeout=timeout)

    async def execute_in_conda_env(self, cmd: str, env, daemon=False) -> str:
        """
        Executes a given command within a specified Conda environment automatically without
        the need for manual activation. Users just need to provide the name of the Conda
        environment and the command to execute.

        Args:
            cmd (str): The command to execute within the Conda environment.
            env (str, optional): The name of the Conda environment to activate before executing the command.
                                 If not specified, the command will run in the current active environment.
            daemon (bool): If True, the command is run in an asynchronous task, similar to `run_command`,
                           affecting error logging and handling in the same manner.

        Returns:
            str: The command's output, or an empty string if `daemon` is True, with output processed
                 asynchronously in that case.

        Note:
            This function wraps `run_command`, prepending the necessary Conda activation commands
            to ensure the specified environment is active for the command's execution.
        """
        # windows & linux conda run
        cmd = f"conda activate {env} && {cmd}" if sys.platform.startswith("win") else f"conda run -n {env} {cmd}"
        return await self.run_command(cmd, daemon=daemon)

    async def get_stdout_output(self) -> str:
        """
        Retrieves all collected output from background running commands and returns it as a string.

        Returns:
            str: The collected output from background running commands, returned as a string.
        """
        output_lines = []
        while not self.stdout_queue.empty():
            line = await self.stdout_queue.get()
            output_lines.append(line)
        return "\n".join(output_lines)

    async def _read_and_process_output(self, cmd, daemon=False, cmd_output: Optional[list] = None) -> str:
        cmd_output = [] if cmd_output is None else cmd_output
        # Bind the process locally: a timeout may replace `self.process` while this reader runs.
        process = self.process
        async with self.observer as observer:
            await observer.async_report(cmd + self.command_terminator, "cmd")
            # report the command
            # Read the output until the unique marker is found.
            # We read bytes directly from stdout instead of text because when reading text,
            # '\r' is changed to '\n', resulting in excessive output.
            tmp = b""
            while True:
                chunk = await process.stdout.read(1)
                if not chunk:
                    # EOF: the shell is gone, so the marker will never arrive. Flush whatever is
                    # buffered and stop instead of spinning on an empty read forever.
                    logger.warning(f"The terminal exited before the command completed: {cmd}")
                    lines, tmp = ([tmp], b"") if tmp else ([], b"")
                else:
                    lines = (tmp + chunk).splitlines(True)
                    if lines[-1].endswith(b"\n"):
                        # The buffer ends on a complete line, so every line can be processed.
                        # Note: `*lines, tmp = ...` would move that last line into `tmp` instead,
                        # hiding the end-of-command marker and hanging forever (#2110).
                        tmp = b""
                    else:
                        # Keep the unterminated remainder buffered until the rest arrives.
                        *lines, tmp = lines
                for line in lines:
                    line = line.decode(errors="ignore")
                    ix = line.rfind(END_MARKER_VALUE)
                    if ix >= 0:
                        line = line[:ix]
                        if line:
                            await observer.async_report(line, "output")
                            # report stdout in real-time
                            cmd_output.append(line)
                        return "".join(cmd_output)
                    # log stdout in real-time
                    await observer.async_report(line, "output")
                    cmd_output.append(line)
                    if daemon:
                        await self.stdout_queue.put(line)
                if not chunk:
                    return "".join(cmd_output)

    async def _terminate_process(self):
        """Kill the persistent shell process so that the next command starts a fresh one."""
        process, self.process = self.process, None
        if process is None or process.returncode is not None:
            return
        try:
            process.kill()
        except ProcessLookupError:
            return
        if process.stdin is not None:
            # Release the pipes now, otherwise they are closed during GC, possibly after the event
            # loop is gone, which surfaces as a "RuntimeError: Event loop is closed".
            process.stdin.close()
        await process.wait()
        transport = getattr(process, "_transport", None)
        if transport is not None:
            transport.close()

    async def close(self):
        """Close the persistent shell process."""
        if self.process:
            self.process.stdin.close()
            await self.process.wait()


@register_tool(include_functions=["run"])
class Bash(Terminal):
    """
    A class to run bash commands directly and provides custom shell functions.
    All custom functions in this class can ONLY be called via the `Bash.run` method.
    """

    def __init__(self):
        """init"""
        os.environ["SWE_CMD_WORK_DIR"] = str(Config.default().workspace.path)
        super().__init__()
        self.start_flag = False

    async def start(self):
        await self.run_command(f"cd {Config.default().workspace.path}")
        await self.run_command(f"source {SWE_SETUP_PATH}")

    async def run(self, cmd) -> str:
        """
        Executes a bash command.

        Args:
            cmd (str): The bash command to execute.

        Returns:
            str: The output of the command.

        This method allows for executing standard bash commands as well as
        utilizing several custom shell functions defined in the environment.

        Custom Shell Functions:

        - open <path> [<line_number>]
          Opens the file at the given path in the editor. If line_number is provided,
          the window will move to include that line.
          Arguments:
              path (str): The path to the file to open.
              line_number (int, optional): The line number to move the window to.
              If not provided, the window will start at the top of the file.

        - goto <line_number>
          Moves the window to show <line_number>.
          Arguments:
              line_number (int): The line number to move the window to.

        - scroll_down
          Moves the window down {WINDOW} lines.

        - scroll_up
          Moves the window up {WINDOW} lines.

        - create <filename>
          Creates and opens a new file with the given name.
          Arguments:
              filename (str): The name of the file to create.

        - search_dir_and_preview <search_term> [<dir>]
          Searches for search_term in all files in dir and gives their code preview
          with line numbers. If dir is not provided, searches in the current directory.
          Arguments:
              search_term (str): The term to search for.
              dir (str, optional): The directory to search in. Defaults to the current directory.

        - search_file <search_term> [<file>]
          Searches for search_term in file. If file is not provided, searches in the current open file.
          Arguments:
              search_term (str): The term to search for.
              file (str, optional): The file to search in. Defaults to the current open file.

        - find_file <file_name> [<dir>]
          Finds all files with the given name in dir. If dir is not provided, searches in the current directory.
          Arguments:
              file_name (str): The name of the file to search for.
              dir (str, optional): The directory to search in. Defaults to the current directory.

        - edit <start_line>:<end_line> <<EOF
          <replacement_text>
          EOF
          Line numbers start from 1. Replaces lines <start_line> through <end_line> (inclusive) with the given text in the open file.
          The replacement text is terminated by a line with only EOF on it. All of the <replacement text> will be entered, so make
          sure your indentation is formatted properly. Python files will be checked for syntax errors after the edit. If the system
          detects a syntax error, the edit will not be executed. Simply try to edit the file again, but make sure to read the error
          message and modify the edit command you issue accordingly. Issuing the same command a second time will just lead to the same
          error message again. All code modifications made via the 'edit' command must strictly follow the PEP8 standard.
          Arguments:
              start_line (int): The line number to start the edit at, starting from 1.
              end_line (int): The line number to end the edit at (inclusive), starting from 1.
              replacement_text (str): The text to replace the current selection with, must conform to PEP8 standards.

        - submit
          Submits your current code locally. it can only be executed once, the last action before the `end`.

        Note: Make sure to use these functions as per their defined arguments and behaviors.
        """
        if not self.start_flag:
            await self.start()
            self.start_flag = True

        return await self.run_command(cmd)
