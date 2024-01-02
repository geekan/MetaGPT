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
from metagpt.config import CONFIG
from metagpt.const import GRAPH_REPO_FILE_REPO
from metagpt.llm import LLM


@pytest.mark.asyncio
async def test_rebuild():
    action = RebuildClassView(
        name="RedBean", context=str(Path(__file__).parent.parent.parent.parent / "metagpt"), llm=LLM()
    )
    await action.run()
    graph_file_repo = CONFIG.git_repo.new_file_repository(relative_path=GRAPH_REPO_FILE_REPO)
    assert graph_file_repo.changed_files


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
