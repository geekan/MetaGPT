import pytest

from metagpt.const import DATA_PATH, METAGPT_ROOT
from metagpt.utils.report import END_MARKER_VALUE
from metagpt.tools.libs.terminal import Terminal


class _FakeStdout:
    def __init__(self, data: bytes):
        self._chunks = iter(data)

    async def read(self, _size: int) -> bytes:
        return bytes([next(self._chunks)]) if self._chunks else b""


class _FakeProcess:
    def __init__(self, data: bytes):
        self.stdout = _FakeStdout(data)


class _FakeObserver:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def async_report(self, *_args):
        return None


@pytest.mark.asyncio
async def test_terminal_returns_when_marker_is_final_line(monkeypatch):
    terminal = Terminal()
    terminal.process = _FakeProcess(b"output\n" + END_MARKER_VALUE)
    monkeypatch.setattr(terminal, "observer", _FakeObserver())

    output = await terminal._read_and_process_output("echo output")

    assert output == "output\n"


@pytest.mark.asyncio
async def test_terminal():
    terminal = Terminal()

    await terminal.run_command(f"cd {METAGPT_ROOT}")
    output = await terminal.run_command("pwd")
    assert output.strip() == str(METAGPT_ROOT)

    # pwd now should be METAGPT_ROOT, cd data should land in DATA_PATH
    await terminal.run_command("cd data")
    output = await terminal.run_command("pwd")
    assert output.strip() == str(DATA_PATH)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
