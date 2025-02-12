#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from metagpt.tools.libs.shell import shell_execute


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["command", "expect_stdout", "expect_stderr"],
    [
        (["file", f"{__file__}"], "Python script text executable, ASCII text", ""),
        (f"file {__file__}", "Python script text executable, ASCII text", ""),
    ],
)
async def test_shell(command, expect_stdout, expect_stderr):
    stdout, stderr, returncode = await shell_execute(command)
    assert returncode == 0
    assert expect_stdout in stdout
    assert stderr == expect_stderr


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
