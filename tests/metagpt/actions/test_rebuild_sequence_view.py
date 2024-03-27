#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4
@Author  : mashenquan
@File    : test_rebuild_sequence_view.py
@Desc    : Unit tests for reconstructing the sequence diagram from a source code project.
"""
from pathlib import Path

import pytest

from metagpt.actions.rebuild_sequence_view import RebuildSequenceView
from metagpt.const import GRAPH_REPO_FILE_REPO
from metagpt.llm import LLM
from metagpt.utils.common import aread
from metagpt.utils.git_repository import ChangeType
from metagpt.utils.graph_repository import SPO


@pytest.mark.skip
@pytest.mark.asyncio
async def test_rebuild(context, mocker):
    # Mock
    data = await aread(filename=Path(__file__).parent / "../../data/graph_db/networkx.class_view.json")
    graph_db_filename = Path(context.repo.workdir.name).with_suffix(".json")
    await context.repo.docs.graph_repo.save(filename=str(graph_db_filename), content=data)
    context.git_repo.add_change({f"{GRAPH_REPO_FILE_REPO}/{graph_db_filename}": ChangeType.UNTRACTED})
    context.git_repo.commit("commit1")
    # mock_spo = SPO(
    #     subject="metagpt/startup.py:__name__:__main__",
    #     predicate="has_page_info",
    #     object_='{"lineno":78,"end_lineno":79,"type_name":"ast.If","tokens":["__name__","__main__"],"properties":{}}',
    # )
    mock_spo = SPO(
        subject="metagpt/management/skill_manager.py:__name__:__main__",
        predicate="has_page_info",
        object_='{"lineno":113,"end_lineno":116,"type_name":"ast.If","tokens":["__name__","__main__"],"properties":{}}',
    )
    mocker.patch.object(RebuildSequenceView, "_search_main_entry", return_value=[mock_spo])

    action = RebuildSequenceView(
        name="RedBean",
        i_context=str(
            Path(__file__).parent.parent.parent.parent / "metagpt/management/skill_manager.py:__name__:__main__"
        ),
        llm=LLM(),
        context=context,
    )
    await action.run()
    rows = await action.graph_db.select()
    assert rows
    assert context.repo.docs.graph_repo.changed_files


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
