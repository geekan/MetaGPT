import pytest

from metagpt.const import DATA_PATH, METAGPT_ROOT
from metagpt.tools.libs.terminal import Terminal


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
