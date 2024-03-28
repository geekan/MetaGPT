#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from pydantic import BaseModel

from metagpt.tools.libs.git import git_checkout, git_clone
from metagpt.utils.git_repository import GitRepository


class SWEBenchItem(BaseModel):
    base_commit: str
    repo: str


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["url", "commit_id"], [("https://github.com/sqlfluff/sqlfluff.git", "d19de0ecd16d298f9e3bfb91da122734c40c01e5")]
)
async def test_git(url: str, commit_id: str):
    repo_dir = await git_clone(url)
    assert repo_dir

    await git_checkout(repo_dir, commit_id)

    repo = GitRepository(repo_dir, auto_init=False)
    repo.delete_repository()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
