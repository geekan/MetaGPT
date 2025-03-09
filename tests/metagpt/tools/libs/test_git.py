#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import uuid

import pytest
from github import Auth, Github
from pydantic import BaseModel

from metagpt.context import Context
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.schema import UserMessage
from metagpt.utils.common import awrite
from metagpt.utils.git_repository import GitRepository


class SWEBenchItem(BaseModel):
    base_commit: str
    repo: str


async def get_env(key: str, app_name: str = ""):
    return os.environ.get(key)


@pytest.mark.skip
@pytest.mark.asyncio
async def test_login():
    auth = Auth.Login(await get_env("GITHUB_USER"), await get_env("GITHUB_PWD"))
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
        access_token=await get_env(key="access_token", app_name="github"),
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
        base_repo_name="iorisa/MetaGPT",
        base="send18",
        head="fixbug/gbk",
        title="Test pr",
        body=body,
        access_token=await get_env(key="access_token", app_name="github"),
    )
    print(pr)
    assert pr


@pytest.mark.skip
@pytest.mark.asyncio
async def test_new_pr1():
    body = """
    >>> SUMMARY
    >>> Change HTTP library used to send requests
    >>>
    >>> TESTS
    >>>   - [x] Send 'GET' request
    >>>   - [x] Send 'POST' request with/without body
    """
    pr = await GitRepository.create_pull(
        head_repo_name="iorisa/MetaGPT",
        head="fixbug/vscode",
        base_repo_name="send18/MetaGPT",
        base="dev",
        title="Test pr",
        body=body,
        access_token=await get_env(key="access_token", app_name="github"),
    )
    print(pr)
    assert pr


@pytest.mark.skip
@pytest.mark.asyncio
async def test_auth():
    access_token = await get_env(key="access_token", app_name="github")
    auth = Auth.Token(access_token)
    g = Github(auth=auth)
    u = g.get_user()
    v = u.get_repos(visibility="public")
    a = [i.full_name for i in v]
    assert a
    print(a)
    pass


@pytest.mark.skip
@pytest.mark.asyncio
async def test_github(context):
    repo = await GitRepository.clone_from(url="https://github.com/iorisa/snake-game.git")
    content = uuid.uuid4().hex
    await awrite(filename=repo.workdir / "README.md", data=content)
    branch = await repo.push(
        new_branch=f"feature/{content[0:8]}", access_token=await get_env(key="access_token", app_name="github")
    )
    pr = await GitRepository.create_pull(
        base=branch.base,
        head=branch.head,
        base_repo_name=branch.repo_name,
        title=f"new pull {content[0:8]}",
        access_token=await get_env(key="access_token", app_name="github"),
    )
    assert pr


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content",
    [
        # "create a new issue to github repo 'iorisa/snake-game' :'The snake did not grow longer after eating'",
        "Resolve the issue #1 'Snake not growing longer after eating' in the GitHub repository https://github.com/iorisa/snake-game.git', and create a new pull request about the issue"
    ],
)
async def test_git_create_issue(content: str):
    context = Context()
    di = DataInterpreter(context=context, tools=["<all>"])

    prerequisite = "from metagpt.tools.libs import get_env"
    await di.execute_code.run(code=prerequisite, language="python")
    di.put_message(UserMessage(content=content))
    while not di.is_idle:
        await di.run()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
