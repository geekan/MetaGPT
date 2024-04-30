#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

import pytest
from github import Auth, Github
from pydantic import BaseModel

from metagpt.tools.libs.git import git_checkout, git_clone
from metagpt.utils.git_repository import GitRepository


class SWEBenchItem(BaseModel):
    base_commit: str
    repo: str


def get_env(key):
    return os.environ.get(key)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["url", "commit_id"], [("https://github.com/sqlfluff/sqlfluff.git", "d19de0ecd16d298f9e3bfb91da122734c40c01e5")]
)
@pytest.mark.skip
async def test_git(url: str, commit_id: str):
    repo_dir = await git_clone(url)
    assert repo_dir

    await git_checkout(repo_dir, commit_id)

    repo = GitRepository(repo_dir, auto_init=False)
    repo.delete_repository()


@pytest.mark.skip
def test_login():
    auth = Auth.Login(get_env("GITHUB_USER"), get_env("GITHUB_PWD"))
    g = Github(auth=auth)
    repo = g.get_repo("geekan/MetaGPT")
    topics = repo.get_topics()
    assert topics
    open_issues = repo.get_issues(state="open")
    issues = [i for i in open_issues]
    assert issues


@pytest.mark.skip
@pytest.mark.asyncio
async def test_new_issue():
    issue = await GitRepository.create_issue(
        repo_name="iorisa/MetaGPT",
        title="This is a new issue",
        body="This is the issue body",
        access_token=get_env("GITHUB_PERSONAL_ACCESS_TOKEN"),
    )
    print(issue)
    assert issue.number
    pass


@pytest.mark.skip
@pytest.mark.asyncio
async def test_new_pr():
    body = """
    >>> SUMMARY
    >>> Change HTTP library used to send requests
    >>>
    >>> TESTS
    >>>   - [x] Send 'GET' request
    >>>   - [x] Send 'POST' request with/without body
    """
    pr = await GitRepository.create_pull(
        repo_name="iorisa/MetaGPT",
        base="send18",
        head="fixbug/gbk",
        title="Test pr",
        body=body,
        access_token=get_env("GITHUB_PERSONAL_ACCESS_TOKEN"),
    )
    print(pr)
    assert pr


@pytest.mark.skip
def test_auth():
    access_token = get_env("GITHUB_PERSONAL_ACCESS_TOKEN")
    auth = Auth.Token(access_token)
    g = Github(auth=auth)
    u = g.get_user()
    v = u.get_repos(visibility="public")
    a = [i.full_name for i in v]
    assert a
    print(a)
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
