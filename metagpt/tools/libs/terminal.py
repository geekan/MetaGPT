import subprocess

from metagpt.logs import TOOL_LOG_END_MARKER, ToolLogItem, log_tool_output
from metagpt.tools.tool_registry import register_tool


@register_tool()
class Terminal:
    """A tool for running terminal commands. Don't initialize a new instance of this class if one already exists."""

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

    def run_command(self, cmd: str) -> str:
        """
        Run a command in the terminal and return the output.
        When the command is being executed, stream the output to the terminal.
        Maintains state across commands, such as current directory.

        Args:
            cmd (str): The command to run in the terminal.

        Returns:
            str: The output of the terminal command.
        """
        cmd_output = []

        # Send the command
        self.process.stdin.write(cmd + self.command_terminator)
        self.process.stdin.write(
            f'echo "{TOOL_LOG_END_MARKER.value}"' + self.command_terminator  # write EOF
        )  # Unique marker to signal command end
        self.process.stdin.flush()
        log_tool_output(
            output=ToolLogItem(name="cmd", value=cmd + self.command_terminator), tool_name="Terminal"
        )  # log the command

        # Read the output until the unique marker is found
        while True:
            line = self.process.stdout.readline()
            ix = line.rfind(TOOL_LOG_END_MARKER.value)
            if ix >= 0:
                line = line[0:ix]
                if line:
                    log_tool_output(
                        output=ToolLogItem(name="output", value=line), tool_name="Terminal"
                    )  # log stdout in real-time
                    cmd_output.append(line)
                log_tool_output(TOOL_LOG_END_MARKER)
                break
            log_tool_output(
                output=ToolLogItem(name="output", value=line), tool_name="Terminal"
            )  # log stdout in real-time
            cmd_output.append(line)

        return "".join(cmd_output)

    def close(self):
        """Close the persistent shell process."""
        self.process.stdin.close()
        self.process.terminate()
        self.process.wait()
