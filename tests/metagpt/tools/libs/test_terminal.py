import asyncio

import pytest

from metagpt.const import DATA_PATH, METAGPT_ROOT
from metagpt.tools.libs.terminal import Terminal
from metagpt.utils.report import END_MARKER_VALUE


class _FakeStdin:
    """Collects everything the terminal writes to the shell."""

    def __init__(self):
        self.data = b""

    def write(self, data: bytes):
        self.data += data

    async def drain(self):
        return None

    def close(self):
        return None


class _FakeStdout:
    """Replays a fixed byte sequence, returning b"" at EOF like `StreamReader.read`."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    async def read(self, n: int = -1) -> bytes:
        if self.pos >= len(self.data):
            return b""
        chunk = self.data[self.pos : self.pos + n] if n >= 0 else self.data[self.pos :]
        self.pos += len(chunk)
        return chunk


class _NeverEndingStdout:
    """A shell that produces nothing, like a command that never returns."""

    async def read(self, n: int = -1) -> bytes:
        await asyncio.sleep(3600)


class _FakeProcess:
    def __init__(self, stdout):
        self.stdin = _FakeStdin()
        self.stdout = stdout
        self.returncode = None
        self.killed = False

    def kill(self):
        self.killed = True
        self.returncode = -9

    async def wait(self):
        return self.returncode


def _terminal_with_output(stdout) -> Terminal:
    terminal = Terminal()
    terminal.process = _FakeProcess(stdout)
    return terminal


@pytest.mark.asyncio
async def test_terminal():
    terminal = Terminal()

    try:
        # The timeouts turn a regression of #2110 into a failure instead of a hang.
        await asyncio.wait_for(terminal.run_command(f"cd {METAGPT_ROOT}"), timeout=30)
        output = await asyncio.wait_for(terminal.run_command("pwd"), timeout=30)
        assert output.strip() == str(METAGPT_ROOT)

        # pwd now should be METAGPT_ROOT, cd data should land in DATA_PATH
        await asyncio.wait_for(terminal.run_command("cd data"), timeout=30)
        output = await asyncio.wait_for(terminal.run_command("pwd"), timeout=30)
        assert output.strip() == str(DATA_PATH)
    finally:
        await terminal.close()


@pytest.mark.asyncio
async def test_run_command_returns_when_marker_ends_the_buffer():
    """Regression test for #2110.

    The end marker is the last line the shell writes, so the read buffer ends on a newline.
    `*lines, tmp = output.splitlines(True)` used to move that line into `tmp` instead of
    yielding it, so the marker was never seen and `run_command` waited forever.
    """
    terminal = _terminal_with_output(_FakeStdout(f"/workspace\n{END_MARKER_VALUE}".encode()))

    output = await asyncio.wait_for(terminal.run_command("pwd"), timeout=5)

    assert output == "/workspace\n"


@pytest.mark.asyncio
async def test_run_command_keeps_carriage_returns():
    r"""Lines are split on newlines only, so '\r' progress output is preserved verbatim."""
    terminal = _terminal_with_output(_FakeStdout(f"50%\r100%\r\ndone\n{END_MARKER_VALUE}".encode()))

    output = await asyncio.wait_for(terminal.run_command("progress"), timeout=5)

    assert output == "50%\r100%\r\ndone\n"


@pytest.mark.asyncio
async def test_run_command_returns_output_without_trailing_newline():
    """Output that does not end with a newline is flushed together with the marker line."""
    terminal = _terminal_with_output(_FakeStdout(f"no-newline{END_MARKER_VALUE}".encode()))

    output = await asyncio.wait_for(terminal.run_command("printf no-newline"), timeout=5)

    assert output == "no-newline"


@pytest.mark.asyncio
async def test_run_command_returns_at_eof():
    """A dead shell can no longer emit the marker, so return the partial output instead of looping."""
    terminal = _terminal_with_output(_FakeStdout(b"partial\n"))

    output = await asyncio.wait_for(terminal.run_command("exit"), timeout=5)

    assert output == "partial\n"


@pytest.mark.asyncio
async def test_run_command_times_out_and_resets_the_terminal():
    """A command that never completes must fail visibly instead of hanging the agent."""
    terminal = _terminal_with_output(_NeverEndingStdout())
    process = terminal.process

    output = await asyncio.wait_for(terminal.run_command("sleep 1000", timeout=0.1), timeout=5)

    assert "[Terminal timeout]" in output
    assert process.killed
    # The shell is gone, so the next command starts a fresh session.
    assert terminal.process is None


@pytest.mark.asyncio
async def test_run_command_keeps_partial_output_on_timeout():
    """Whatever the command printed before the timeout is still reported back."""

    class _StalledStdout(_FakeStdout):
        async def read(self, n: int = -1) -> bytes:
            chunk = await super().read(n)
            if not chunk:
                await asyncio.sleep(3600)
            return chunk

    terminal = _terminal_with_output(_StalledStdout(b"started\n"))

    output = await asyncio.wait_for(terminal.run_command("long-command", timeout=0.1), timeout=5)

    assert output.startswith("started\n")
    assert "[Terminal timeout]" in output


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
