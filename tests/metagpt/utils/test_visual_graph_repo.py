#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4
@Author  : mashenquan
@File    : test_visual_graph_repo.py
@Desc    : Unit tests for testing and demonstrating the usage of VisualDiGraphRepo.
"""

import re
from pathlib import Path

import pytest

from metagpt.utils.common import remove_affix, split_namespace
from metagpt.utils.visual_graph_repo import VisualDiGraphRepo


@pytest.mark.asyncio
async def test_visual_di_graph_repo(context, mocker):
    filename = Path(__file__).parent / "../../data/graph_db/networkx.sequence_view.json"
    repo = await VisualDiGraphRepo.load_from(filename=filename)

    class_view = await repo.get_mermaid_class_view()
    assert class_view
    await context.repo.resources.graph_repo.save(filename="class_view.md", content=f"```mermaid\n{class_view}\n```\n")

    sequence_views = await repo.get_mermaid_sequence_views()
    assert sequence_views
    for ns, sqv in sequence_views:
        filename = re.sub(r"[:/\\\.]+", "_", ns) + ".sequence_view.md"
        sqv = sqv.strip(" `")
        await context.repo.resources.graph_repo.save(filename=filename, content=f"```mermaid\n{sqv}\n```\n")

    sequence_view_vers = await repo.get_mermaid_sequence_view_versions()
    assert sequence_view_vers
    for ns, sqv in sequence_view_vers:
        ver, sqv = split_namespace(sqv)
        filename = re.sub(r"[:/\\\.]+", "_", ns) + f".{ver}.sequence_view_ver.md"
        sqv = remove_affix(sqv).strip(" `")
        await context.repo.resources.graph_repo.save(filename=filename, content=f"```mermaid\n{sqv}\n```\n")


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
