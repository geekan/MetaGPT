#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19
@Author  : mashenquan
@File    : test_di_graph_repository.py
@Desc    : Unit tests for di_graph_repository.py
"""

from pathlib import Path

import pytest
from pydantic import BaseModel

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.repo_parser import RepoParser
from metagpt.utils.common import concat_namespace
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.graph_repository import GraphKeyword


@pytest.mark.asyncio
async def test_di_graph_repository():
    class Input(BaseModel):
        s: str
        p: str
        o: str

    inputs = [
        {"s": "main.py:Game:draw", "p": "method:hasDescription", "o": "Draw image"},
        {"s": "main.py:Game:draw", "p": "method:hasDescription", "o": "Show image"},
    ]
    path = Path(__file__).parent
    graph = DiGraphRepository(name="test", root=path)
    for i in inputs:
        data = Input(**i)
        await graph.insert(subject=data.s, predicate=data.p, object_=data.o)
        v = graph.json()
        assert v
    await graph.save()
    assert graph.pathname.exists()
    graph.pathname.unlink()


@pytest.mark.asyncio
async def test_js_parser():
    class Input(BaseModel):
        path: str

    inputs = [
        {"path": str(Path(__file__).parent / "../../data/code")},
    ]
    path = Path(__file__).parent
    graph = DiGraphRepository(name="test", root=path)
    for i in inputs:
        data = Input(**i)
        repo_parser = RepoParser(base_directory=data.path)
        symbols = repo_parser.generate_symbols()
        for s in symbols:
            ns = s.get("file", "")
            for c in s.get("classes", []):
                await graph.insert(
                    subject=concat_namespace(ns, c), predicate=GraphKeyword.IS.value, object_=GraphKeyword.CLASS.value
                )
            for f in s.get("functions", []):
                await graph.insert(
                    subject=concat_namespace(ns, f),
                    predicate=GraphKeyword.IS.value,
                    object_=GraphKeyword.FUNCTION.value,
                )
            for g in s.get("globals", []):
                await graph.insert(
                    subject=concat_namespace(ns, g),
                    predicate=GraphKeyword.IS.value,
                    object_=GraphKeyword.GLOBAL_VARIABLE.value,
                )
    data = graph.json()
    assert data


@pytest.mark.asyncio
async def test_codes():
    path = DEFAULT_WORKSPACE_ROOT / "snake_game"
    repo_parser = RepoParser(base_directory=path)

    graph = DiGraphRepository(name="test", root=path)
    symbols = repo_parser.generate_symbols()
    for s in symbols:
        ns = s.get("file", "")
        for c in s.get("classes", []):
            class_name = c.get("name", "")
            await graph.insert(
                subject=ns, predicate=GraphKeyword.HAS_CLASS.value, object_=concat_namespace(ns, class_name)
            )
            await graph.insert(
                subject=concat_namespace(ns, class_name),
                predicate=GraphKeyword.IS.value,
                object_=GraphKeyword.CLASS.value,
            )
            methods = c.get("methods", [])
            for fn in methods:
                await graph.insert(
                    subject=concat_namespace(ns, class_name, fn),
                    predicate=GraphKeyword.IS.value,
                    object_=GraphKeyword.CLASS_FUNCTION.value,
                )
        for f in s.get("functions", []):
            await graph.insert(
                subject=concat_namespace(ns, f), predicate=GraphKeyword.IS.value, object_=GraphKeyword.FUNCTION.value
            )
        for g in s.get("globals", []):
            await graph.insert(
                subject=concat_namespace(ns, g),
                predicate=GraphKeyword.IS.value,
                object_=GraphKeyword.GLOBAL_VARIABLE.value,
            )
    data = graph.json()
    assert data
    print(data)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
