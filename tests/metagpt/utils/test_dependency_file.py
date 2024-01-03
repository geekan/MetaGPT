#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/22
@Author  : mashenquan
@File    : test_dependency_file.py
@Desc: Unit tests for dependency_file.py
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Set, Union

import pytest
from pydantic import BaseModel

from metagpt.utils.dependency_file import DependencyFile


@pytest.mark.asyncio
async def test_dependency_file():
    class Input(BaseModel):
        x: Union[Path, str]
        deps: Optional[Set[Union[Path, str]]] = None
        key: Optional[Union[Path, str]] = None
        want: Set[str]

    inputs = [
        Input(x="a/b.txt", deps={"c/e.txt", Path(__file__).parent / "d.txt"}, want={"c/e.txt", "d.txt"}),
        Input(
            x=Path(__file__).parent / "x/b.txt",
            deps={"s/e.txt", Path(__file__).parent / "d.txt"},
            key="x/b.txt",
            want={"s/e.txt", "d.txt"},
        ),
        Input(x="f.txt", deps=None, want=set()),
        Input(x="a/b.txt", deps=None, want=set()),
    ]

    file = DependencyFile(workdir=Path(__file__).parent)

    for i in inputs:
        await file.update(filename=i.x, dependencies=i.deps)
        assert await file.get(filename=i.key or i.x) == i.want

    file2 = DependencyFile(workdir=Path(__file__).parent)
    file2.delete_file()
    assert not file.exists
    await file2.update(filename="a/b.txt", dependencies={"c/e.txt", Path(__file__).parent / "d.txt"}, persist=False)
    assert not file.exists
    await file2.save()
    assert file2.exists

    file1 = DependencyFile(workdir=Path(__file__).parent)
    assert file1.exists
    assert await file1.get("a/b.txt", persist=False) == set()
    assert await file1.get("a/b.txt") == {"c/e.txt", "d.txt"}
    await file1.load()
    assert await file1.get("a/b.txt") == {"c/e.txt", "d.txt"}
    file1.delete_file()
    assert not file.exists


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
