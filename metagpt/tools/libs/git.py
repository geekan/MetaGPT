#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from github.Issue import Issue
from github.PullRequest import PullRequest

from metagpt.tools.tool_registry import register_tool


@register_tool(tags=["software development", "git", "Push to remote git repository."])
async def git_push(
    local_path: Union[str, Path],
    app_name: str,
    comments: str = "Commit",
    new_branch: str = "",
) -> "GitBranch":
    """
    Pushes changes from a local Git repository to its remote counterpart.

    Args:
        local_path (Union[str, Path]): The absolute path to the local Git repository.
        app_name (str): The name of the platform hosting the repository (e.g., "github", "gitlab", "bitbucket").
        comments (str, optional): Comments to be associated with the push. Defaults to "Commit".
        new_branch (str, optional): The name of the new branch to create and push changes to.
            If not provided, changes will be pushed to the current branch. Defaults to "".

    Returns:
        GitBranch: The branch to which the changes were pushed.

    Raises:
        ValueError: If the provided local_path does not point to a valid Git repository.

    Example:
        >>> url = "https://github.com/iorisa/snake-game.git"
        >>> local_path = await git_clone(url=url)
        >>> app_name = "github"
        >>> comments = "Commit"
        >>> new_branch = "feature/new"
        >>> branch = await git_push(local_path=local_path, app_name=app_name, comments=comments, new_branch=new_branch)
        >>> base = branch.base
        >>> head = branch.head
        >>> repo_name = branch.repo_name
        >>> print(f"base branch:'{base}', head branch:'{head}', repo_name:'{repo_name}'")
        base branch:'master', head branch:'feature/new', repo_name:'iorisa/snake-game'
    """

    from metagpt.tools.libs import get_env
    from metagpt.utils.git_repository import GitRepository

    if not GitRepository.is_git_dir(local_path):
        raise ValueError("Invalid local git repository")

    repo = GitRepository(local_path=local_path, auto_init=False)
    # Read access token from environment variables.
    access_token = await get_env(key="access_token", app_name=app_name)
    branch = await repo.push(new_branch=new_branch, comments=comments, access_token=access_token)
    return branch


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

    from metagpt.tools.libs import get_env
    from metagpt.utils.git_repository import GitRepository

    access_token = await get_env(key="access_token", app_name=app_name)
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
