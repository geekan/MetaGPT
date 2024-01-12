#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4
@Author  : mashenquan
@File    : test_rebuild_sequence_view.py
"""
from pathlib import Path

import pytest

from metagpt.actions.rebuild_sequence_view import RebuildSequenceView
from metagpt.const import GRAPH_REPO_FILE_REPO
from metagpt.context import CONTEXT
from metagpt.llm import LLM
from metagpt.utils.common import aread
from metagpt.utils.git_repository import ChangeType
from metagpt.utils.project_repo import ProjectRepo


@pytest.mark.asyncio
async def test_rebuild():
    # Mock
    data = await aread(filename=Path(__file__).parent / "../../data/graph_db/networkx.json")
    graph_db_filename = Path(CONTEXT.git_repo.workdir.name).with_suffix(".json")
    project_repo = ProjectRepo(CONTEXT.git_repo)
    await project_repo.docs.graph_repo.save(filename=str(graph_db_filename), content=data)
    CONTEXT.git_repo.add_change({f"{GRAPH_REPO_FILE_REPO}/{graph_db_filename}": ChangeType.UNTRACTED})
    CONTEXT.git_repo.commit("commit1")

    action = RebuildSequenceView(
        name="RedBean", i_context=str(Path(__file__).parent.parent.parent.parent / "metagpt"), llm=LLM()
    )
    await action.run()
    assert project_repo.docs.graph_repo.changed_files


@pytest.mark.parametrize(
    ("root", "pathname", "want"),
    [
        (Path(__file__).parent.parent.parent, "/".join(__file__.split("/")[-2:]), Path(__file__)),
        (Path(__file__).parent.parent.parent, "f/g.txt", None),
    ],
)
def test_get_full_filename(root, pathname, want):
    res = RebuildSequenceView._get_full_filename(root=root, pathname=pathname)
    assert res == want


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
