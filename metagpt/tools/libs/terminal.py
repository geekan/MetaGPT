import subprocess
import threading
from queue import Queue

from metagpt.logs import TOOL_LOG_END_MARKER, ToolLogItem, log_tool_output
from metagpt.tools.tool_registry import register_tool


@register_tool()
class Terminal:
    """
    A tool for running terminal commands.
    Don't initialize a new instance of this class if one already exists.
    For commands that need to be executed within a Conda environment, it is recommended
    to use the `execute_in_conda_env` method.
    """

    def __init__(self):
        self.shell_command = ["bash"]  # FIXME: should consider windows support later
        self.command_terminator = "\n"

        # Start a persistent shell process
        self.process = subprocess.Popen(
            self.shell_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
        )
        self.stdout_queue = Queue()

    def run_command(self, cmd: str, daemon=False) -> str:
        """
        Executes a specified command in the terminal and streams the output back in real time.
        This command maintains state across executions, such as the current directory,
        allowing for sequential commands to be contextually aware. The output from the
        command execution is placed into `stdout_queue`, which can be consumed as needed.

        Args:
            cmd (str): The command to execute in the terminal.
            daemon (bool): If True, executes the command in a background thread, allowing
                           the main program to continue execution. The command's output is
                           collected asynchronously in daemon mode and placed into `stdout_queue`.

        Returns:
            str: The command's output or an empty string if `daemon` is True. Remember that
                 when `daemon` is True, the output is collected into `stdout_queue` and must
                 be consumed from there.

        Note:
            If `stdout_queue` is not periodically consumed, it could potentially grow indefinitely,
            consuming memory. Ensure that there's a mechanism in place to consume this queue,
            especially during long-running or output-heavy command executions.
        """

        # Send the command
        self.process.stdin.write(cmd + self.command_terminator)
        self.process.stdin.write(
            f'echo "{TOOL_LOG_END_MARKER.value}"' + self.command_terminator
        )  # Unique marker to signal command end
        self.process.stdin.flush()
        if daemon:
            threading.Thread(target=self._read_and_process_output, args=(cmd,), daemon=True).start()
            return ""
        else:
            return self._read_and_process_output(cmd)

    def execute_in_conda_env(self, cmd: str, env, daemon=False) -> str:
        """
        Executes a given command within a specified Conda environment automatically without
        the need for manual activation. Users just need to provide the name of the Conda
        environment and the command to execute.

        Args:
            cmd (str): The command to execute within the Conda environment.
            env (str, optional): The name of the Conda environment to activate before executing the command.
                                 If not specified, the command will run in the current active environment.
            daemon (bool): If True, the command is run in a background thread, similar to `run_command`,
                           affecting error logging and handling in the same manner.

        Returns:
            str: The command's output, or an empty string if `daemon` is True, with output processed
                 asynchronously in that case.

        Note:
            This function wraps `run_command`, prepending the necessary Conda activation commands
            to ensure the specified environment is active for the command's execution.
        """
        cmd = f"conda run -n {env} {cmd}"
        return self.run_command(cmd, daemon=daemon)

    def _read_and_process_output(self, cmd):
        cmd_output = []
        log_tool_output(
            output=ToolLogItem(name="cmd", value=cmd + self.command_terminator), tool_name="Terminal"
        )  # log the command

        # Read the output until the unique marker is found
        while True:
            line = self.process.stdout.readline()
            if line.strip() == TOOL_LOG_END_MARKER.value:
                log_tool_output(TOOL_LOG_END_MARKER)
                break
            # log stdout in real-time
            log_tool_output(output=ToolLogItem(name="output", value=line), tool_name="Terminal")
            cmd_output.append(line)
            self.stdout_queue.put(line)

        return "".join(cmd_output)

    def close(self):
        """Close the persistent shell process."""
        self.process.stdin.close()
        self.process.terminate()
        self.process.wait()
