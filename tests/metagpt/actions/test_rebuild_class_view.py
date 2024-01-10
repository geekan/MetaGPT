#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/20
@Author  : mashenquan
@File    : test_rebuild_class_view.py
@Desc    : Unit tests for rebuild_class_view.py
"""
from pathlib import Path

import pytest

from metagpt.actions.rebuild_class_view import RebuildClassView
from metagpt.const import GRAPH_REPO_FILE_REPO
from metagpt.context import CONTEXT
from metagpt.llm import LLM


@pytest.mark.asyncio
async def test_rebuild():
    action = RebuildClassView(
        name="RedBean", i_context=str(Path(__file__).parent.parent.parent.parent / "metagpt"), llm=LLM()
    )
    await action.run()
    graph_file_repo = CONTEXT.git_repo.new_file_repository(relative_path=GRAPH_REPO_FILE_REPO)
    assert graph_file_repo.changed_files


@pytest.mark.parametrize(
    ("path", "direction", "diff", "want"),
    [
        ("metagpt/startup.py", "=", ".", "metagpt/startup.py"),
        ("metagpt/startup.py", "+", "MetaGPT", "MetaGPT/metagpt/startup.py"),
        ("metagpt/startup.py", "-", "metagpt", "startup.py"),
    ],
)
def test_align_path(path, direction, diff, want):
    res = RebuildClassView._align_root(path=path, direction=direction, diff_path=diff)
    assert res == want


@pytest.mark.parametrize(
    ("path_root", "package_root", "want_direction", "want_diff"),
    [
        ("/Users/x/github/MetaGPT/metagpt", "/Users/x/github/MetaGPT/metagpt", "=", "."),
        ("/Users/x/github/MetaGPT", "/Users/x/github/MetaGPT/metagpt", "-", "metagpt"),
        ("/Users/x/github/MetaGPT/metagpt", "/Users/x/github/MetaGPT", "+", "metagpt"),
    ],
)
def test_diff_path(path_root, package_root, want_direction, want_diff):
    direction, diff = RebuildClassView._diff_path(path_root=Path(path_root), package_root=Path(package_root))
    assert direction == want_direction
    assert diff == want_diff


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
