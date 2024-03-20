#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from metagpt.tools.libs import (
    fix_bug,
    git_archive,
    run_qa_test,
    write_codes,
    write_design,
    write_prd,
    write_project_plan,
)


@pytest.mark.asyncio
async def test_software_team():
    path = await write_prd("snake game")
    assert path

    path = await write_design(path)
    assert path

    path = await write_project_plan(path)
    assert path

    path = await write_codes(path)
    assert path

    path = await run_qa_test(path)
    assert path

    issue = """
pygame 2.0.1 (SDL 2.0.14, Python 3.9.17)
Hello from the pygame community. https://www.pygame.org/contribute.html
Traceback (most recent call last):
  File "/Users/ix/github/bak/MetaGPT/workspace/snake_game/snake_game/main.py", line 10, in <module>
    main()
  File "/Users/ix/github/bak/MetaGPT/workspace/snake_game/snake_game/main.py", line 7, in main
    game.start_game()
  File "/Users/ix/github/bak/MetaGPT/workspace/snake_game/snake_game/game.py", line 81, in start_game
    x
NameError: name 'x' is not defined
    """
    path = await fix_bug(path, issue)
    assert path

    new_path = await write_prd("snake game with moving enemy", path)
    assert new_path == path

    git_log = await git_archive(new_path)
    assert git_log


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
