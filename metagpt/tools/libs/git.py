#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import urllib
from pathlib import Path
from typing import Optional

from github.Issue import Issue
from github.PullRequest import PullRequest

from metagpt.tools.tool_registry import register_tool


@register_tool(tags=["software development", "git", "create a git pull request or merge request"])
async def git_create_pull(
    base: str,
    head: str,
    app_name: str,
    base_repo_name: str,
    head_repo_name: str = None,
    title: Optional[str] = None,
    body: Optional[str] = None,
    issue: Optional[Issue] = None,
) -> PullRequest:
    """
    Creates a pull request on a Git repository. Use this tool in priority over Browser to create a pull request.

    Args:
        base (str): The name of the base branch where the pull request will be merged.
        head (str): The name of the branch that contains the changes for the pull request.
        app_name (str): The name of the platform hosting the repository (e.g., "github", "gitlab", "bitbucket").
        base_repo_name (str): The full name of the target repository (in the format "user/repo") where the pull request will be created.
        head_repo_name (Optional[str]): The full name of the source repository (in the format "user/repo") from which the changes will be pulled.
        title (Optional[str]): The title of the pull request. Defaults to None.
        body (Optional[str]): The description or body content of the pull request. Defaults to None.
        issue (Optional[Issue]): An optional issue related to the pull request. Defaults to None.

    Example:
        >>> # create pull request
        >>> base_repo_name = "geekan/MetaGPT"
        >>> head_repo_name = "ioris/MetaGPT"
        >>> base = "master"
        >>> head = "feature/http"
        >>> title = "feat: modify http lib",
        >>> body = "Change HTTP library used to send requests"
        >>> app_name = "github"
        >>> pr = await git_create_pull(
        >>>   base_repo_name=base_repo_name,
        >>>   head_repo_name=head_repo_name,
        >>>   base=base,
        >>>   head=head,
        >>>   title=title,
        >>>   body=body,
        >>>   app_name=app_name,
        >>> )
        >>> if isinstance(pr, PullRequest):
        >>>     print(pr)
        PullRequest("feat: modify http lib")
        >>> if isinstance(pr, str):
        >>>     print(f"Visit this url to create a new pull request: '{pr}'")
        Visit this url to create a new pull request: 'https://github.com/geekan/MetaGPT/compare/master...iorisa:MetaGPT:feature/http'

    Returns:
        PullRequest: The created pull request.
    """
    from metagpt.utils.git_repository import GitRepository

    git_credentials_path = Path.home() / ".git-credentials"
    with open(git_credentials_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        parsed_url = urllib.parse.urlparse(line)
        if app_name in parsed_url.hostname:
            colon_index = parsed_url.netloc.find(":")
            at_index = parsed_url.netloc.find("@")
            access_token = parsed_url.netloc[colon_index + 1 : at_index]
            break
    return await GitRepository.create_pull(
        base=base,
        head=head,
        base_repo_name=base_repo_name,
        head_repo_name=head_repo_name,
        title=title,
        body=body,
        issue=issue,
        access_token=access_token,
    )


@register_tool(tags=["software development", "create a git issue"])
async def git_create_issue(
    repo_name: str,
    title: str,
    access_token: str,
    body: Optional[str] = None,
) -> Issue:
    """
    Creates an issue on a Git repository.

    Args:
        repo_name (str): The name of the repository.
        title (str): The title of the issue.
        access_token (str): The access token for authentication. Use `get_env` to get access token.
        body (Optional[str], optional): The body of the issue. Defaults to None.

    Example:
        >>> repo_name = "geekan/MetaGPT"
        >>> title = "This is a new issue"
        >>> from metagpt.tools.libs import get_env
        >>> access_token = await get_env(key="access_token", app_name="github")
        >>> body = "This is the issue body."
        >>> issue = await git_create_issue(
        >>>   repo_name=repo_name,
        >>>   title=title,
        >>>   access_token=access_token,
        >>>   body=body,
        >>> )
        >>> print(issue)
        Issue("This is a new issue")

    Returns:
        Issue: The created issue.
    """
    from metagpt.utils.git_repository import GitRepository

    return await GitRepository.create_issue(repo_name=repo_name, title=title, body=body, access_token=access_token)
