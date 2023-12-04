#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : test_git_repository.py
@Desc: Unit tests for git_repository.py
"""

import shutil
from pathlib import Path

import aiofiles
import pytest

from metagpt.utils.git_repository import GitRepository


async def mock_file(filename, content=""):
    async with aiofiles.open(str(filename), mode="w") as file:
        await file.write(content)


async def mock_repo(local_path) -> (GitRepository, Path):
    if local_path.exists():
        shutil.rmtree(local_path)
    assert not local_path.exists()
    repo = GitRepository(local_path=local_path, auto_init=True)
    assert local_path.exists()
    assert local_path == repo.workdir
    assert not repo.changed_files

    await mock_file(local_path / "a.txt")
    await mock_file(local_path / "b.txt")
    subdir = local_path / "subdir"
    subdir.mkdir(parents=True, exist_ok=True)
    await mock_file(subdir / "c.txt")
    return repo, subdir


@pytest.mark.asyncio
async def test_git():
    local_path = Path(__file__).parent / "git"
    repo, subdir = await mock_repo(local_path)

    assert len(repo.changed_files) == 3
    repo.add_change(repo.changed_files)
    repo.commit("commit1")
    assert not repo.changed_files

    await mock_file(local_path / "a.txt", "tests")
    await mock_file(subdir / "d.txt")
    rmfile = local_path / "b.txt"
    rmfile.unlink()
    assert repo.status

    assert len(repo.changed_files) == 3
    repo.add_change(repo.changed_files)
    repo.commit("commit2")
    assert not repo.changed_files

    assert repo.status

    repo.delete_repository()
    assert not local_path.exists()


@pytest.mark.asyncio
async def test_git1():
    local_path = Path(__file__).parent / "git1"
    await mock_repo(local_path)

    repo1 = GitRepository(local_path=local_path, auto_init=False)
    assert repo1.changed_files

    repo1.delete_repository()
    assert not local_path.exists()


@pytest.mark.asyncio
async def test_dependency_file():
    local_path = Path(__file__).parent / "git2"
    repo, subdir = await mock_repo(local_path)

    dependancy_file = await repo.get_dependency()
    assert not dependancy_file.exists

    await dependancy_file.update(filename="a/b.txt", dependencies={"c/d.txt", "e/f.txt"})
    assert dependancy_file.exists

    repo.delete_repository()
    assert not dependancy_file.exists


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
