#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : test_file_repository.py
@Desc: Unit tests for file_repository.py
"""
import shutil
from pathlib import Path

import pytest

from metagpt.utils.git_repository import ChangeType, GitRepository
from tests.metagpt.utils.test_git_repository import mock_file


@pytest.mark.asyncio
async def test_file_repo():
    local_path = Path(__file__).parent / "file_repo_git"
    if local_path.exists():
        shutil.rmtree(local_path)

    git_repo = GitRepository(local_path=local_path, auto_init=True)
    assert not git_repo.changed_files

    await mock_file(local_path / "g.txt", "")

    file_repo_path = "file_repo1"
    full_path = local_path / file_repo_path
    assert not full_path.exists()
    file_repo = git_repo.new_file_repository(file_repo_path)
    assert file_repo.workdir == full_path
    assert file_repo.workdir.exists()
    await file_repo.save("a.txt", "AAA")
    await file_repo.save("b.txt", "BBB", [str(full_path / "a.txt"), f"{file_repo_path}/c.txt"])
    doc = await file_repo.get("a.txt")
    assert "AAA" == doc.content
    doc = await file_repo.get("b.txt")
    assert "BBB" == doc.content
    assert {f"{file_repo_path}/a.txt", f"{file_repo_path}/c.txt"} == await file_repo.get_dependency("b.txt")
    assert {"a.txt": ChangeType.UNTRACTED, "b.txt": ChangeType.UNTRACTED} == file_repo.changed_files
    assert {f"{file_repo_path}/a.txt"} == await file_repo.get_changed_dependency("b.txt")
    await file_repo.save("d/e.txt", "EEE")
    assert ["d/e.txt"] == file_repo.get_change_dir_files("d")
    assert set(file_repo.all_files) == {"a.txt", "b.txt", "d/e.txt"}
    await file_repo.delete("d/e.txt")
    await file_repo.delete("d/e.txt")  # delete twice
    assert set(file_repo.all_files) == {"a.txt", "b.txt"}
    await file_repo.delete("b.txt")
    assert set(file_repo.all_files) == {"a.txt"}

    git_repo.delete_repository()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
