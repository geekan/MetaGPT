#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Optional

from github.Issue import Issue
from github.PullRequest import PullRequest

from metagpt.tools.tool_registry import register_tool
from metagpt.utils.git_repository import GitRepository


@register_tool(tags=["git"])
async def git_clone(url: str, output_dir: str | Path = None) -> Path:
    """
    Clones a Git repository from the given URL.

    Args:
        url (str): The URL of the Git repository to clone.
        output_dir (str or Path, optional): The directory where the repository will be cloned.
            If not provided, the repository will be cloned into the current working directory.

    Returns:
        Path: The path to the cloned repository.

    Raises:
        ValueError: If the specified Git root is invalid.

    Example:
        >>> # git clone to /TO/PATH
        >>> url = 'https://github.com/geekan/MetaGPT.git'
        >>> output_dir = "/TO/PATH"
        >>> repo_dir = await git_clone(url=url, output_dir=output_dir)
        >>> print(repo_dir)
        /TO/PATH/MetaGPT

        >>> # git clone to default directory.
        >>> url = 'https://github.com/geekan/MetaGPT.git'
        >>> repo_dir = await git_clone(url)
        >>> print(repo_dir)
        /WORK_SPACE/downloads/MetaGPT
    """
    repo = await GitRepository.clone_from(url, output_dir)
    return repo.workdir


async def git_checkout(repo_dir: str | Path, commit_id: str):
    """
    Checks out a specific commit in a Git repository.

    Args:
        repo_dir (str or Path): The directory containing the Git repository.
        commit_id (str): The ID of the commit to check out.

    Raises:
        ValueError: If the specified Git root is invalid.

    Example:
        >>> repo_dir = '/TO/GIT/REPO'
        >>> commit_id = 'main'
        >>> await git_checkout(repo_dir=repo_dir, commit_id=commit_id)
        git checkout main
    """
    repo = GitRepository(local_path=repo_dir, auto_init=False)
    if not repo.is_valid:
        ValueError(f"Invalid git root: {repo_dir}")
    await repo.checkout(commit_id)


@register_tool(tags=["git"])
async def git_create_pull_request(
    access_token: str,
    base: str,
    head: str,
    base_repo_name: str,
    head_repo_name: Optional[str] = None,
    title: Optional[str] = None,
    body: Optional[str] = None,
) -> PullRequest:
    """
    Creates a pull request in a Git repository.

    Args:
        access_token (str): The access token for authentication.
        base (str): The name of the base branch of the pull request (e.g., 'main', 'master').
        head (str): The name of the head branch of the pull request (e.g., 'feature-branch').
        base_repo_name (str): The full repository name (user/repo) where the pull request will be created.
        head_repo_name (Optional[str], optional): The full repository name (user/repo) where the pull request will merge from. Defaults to None.
        title (Optional[str]): The title of the pull request.
        body (Optional[str]): The body of the pull request.


    Returns:
        PullRequest: The created pull request object.

    Raises:
        ValueError: If `access_token` is invalid. Visit: "https://github.com/settings/tokens"
        Any exceptions that might occur during the pull request creation process.

    Note:
        This function is intended to be used in an asynchronous context (with `await`).

    Example:
        >>> # Merge Request
        >>> repo_name = "user/repo" # "user/repo" for example: "https://github.com/user/repo.git"
        >>> base = "master" # branch that merge to
        >>> head = "feature/new_feature" # branch that merge from
        >>> title = "Implement new feature"
        >>> body = "This pull request adds functionality X, Y, and Z."
        >>> pull_request = await git_create_pull_request(
            repo_name=repo_name,
            base=base,
            head=head,
            title=title,
            body=body,
            access_token=get_env("git_access_token")
        )
        >>> print(pull_request)
        PullRequest(title="Implement new feature", number=26)

        >>> # Pull Request
        >>> base_repo_name = "user1/repo1" # for example: "user1/repo1" from "https://github.com/user1/repo1.git"
        >>> head_repo_name = "user2/repo2" # for example: "user2/repo2" from "https://github.com/user2/repo2.git"
        >>> base = "master" # branch that merge to
        >>> head = "feature/new_feature" # branch that merge from
        >>> title = "Implement new feature"
        >>> body = "This pull request adds functionality X, Y, and Z."
        >>> pull_request = await git_create_pull_request(
            base_repo_name=base_repo_name,
            head_repo_name=head_repo_name,
            base=base,
            head=head,
            title=title,
            body=body,
            access_token=get_env("git_access_token")
        )
        >>> print(pull_request)
        PullRequest(title="Implement new feature", number=26)

    """
    return await GitRepository.create_pull(
        base_repo_name=base_repo_name,
        head_repo_name=head_repo_name,
        base=base,
        head=head,
        title=title,
        body=body,
        access_token=access_token,
    )


@register_tool(tags=["git"])
async def create_issue(
    access_token: str,
    repo_name: str,
    title: str,
    body: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[list[str]] = None,
) -> Issue:
    """
    Creates an issue in the specified repository.

    Args:
        access_token (str): The access token for authentication.
            Visit `https://github.com/settings/tokens` to obtain a personal access token.
            For more authentication options, visit: `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`
        repo_name (str): The full repository name (user/repo) where the issue will be created.
        title (str): The title of the issue.
        body (Optional[str], optional): The body of the issue. Defaults to None.
        assignee (Optional[str], optional): The username of the assignee for the issue. Defaults to None.
        labels (Optional[list[str]], optional): A list of label names to associate with the issue. Defaults to None.


    Returns:
        Issue: The created issue object.

    Example:
        >>> # Create an issue with title and body
        >>> repo_name = "username/repository"
        >>> title = "Bug Report"
        >>> body = "I found a bug in the application."
        >>> issue = await create_issue(
            repo_name=repo_name,
            title=title,
            body=body,
            access_token=get_env("git_access_token")
        )
        >>> print(issue)
        Issue(title="Bug Report", number=26)

        >>> # Create an issue with title, body, assignee, and labels
        >>> repo_name = "username/repository"
        >>> title = "Bug Report"
        >>> body = "I found a bug in the application."
        >>> assignee = "john_doe"
        >>> labels = ["enhancement", "help wanted"]
        >>> issue = await create_issue(
            repo_name=repo_name,
            title=title,
            body=body,
            assignee=assigee,
            labels=labels,
            access_token=get_env("git_access_token")
        )
        >>> print(issue)
        Issue(title="Bug Report", number=26)
    """
    return await GitRepository.create_issue(
        repo_name=repo_name, title=title, body=body, assignee=assignee, labels=labels, access_token=access_token
    )
