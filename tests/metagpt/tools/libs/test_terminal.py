from metagpt.const import DATA_PATH, METAGPT_ROOT
from metagpt.tools.libs.terminal import Terminal


def test_terminal():
    terminal = Terminal()

    terminal.run_command(f"cd {METAGPT_ROOT}")
    output = terminal.run_command("pwd")
    assert output.strip() == str(METAGPT_ROOT)

    # pwd now should be METAGPT_ROOT, cd data should land in DATA_PATH
    terminal.run_command("cd data")
    output = terminal.run_command("pwd")
    assert output.strip() == str(DATA_PATH)
