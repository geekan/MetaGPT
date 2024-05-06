#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from github.Issue import Issue
from github.PullRequest import PullRequest

from metagpt.const import ASSISTANT_ALIAS
from metagpt.logs import ToolLogItem, log_tool_output
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.git_repository import GitBranch, GitRepository


async def import_git_repo(url: str) -> Path:
    """
    Imports a project from a Git website and formats it to MetaGPT project format to enable incremental appending requirements.

    Args:
        url (str): The Git project URL, such as "https://github.com/geekan/MetaGPT.git".

    Returns:
        Path: The path of the formatted project.

    Example:
        # The Git project URL to input
        >>> git_url = "https://github.com/geekan/MetaGPT.git"

        # Import the Git repository and get the formatted project path
        >>> formatted_project_path = await import_git_repo(git_url)
        >>> print("Formatted project path:", formatted_project_path)
        /PATH/TO/THE/FORMMATTED/PROJECT
    """
    from metagpt.actions.import_repo import ImportRepo
    from metagpt.context import Context

    log_tool_output(
        output=[ToolLogItem(name=ASSISTANT_ALIAS, value=import_git_repo.__name__)], tool_name=import_git_repo.__name__
    )

    ctx = Context()
    action = ImportRepo(repo_path=url, context=ctx)
    await action.run()

    outputs = [ToolLogItem(name="MetaGPT Project", value=str(ctx.repo.workdir))]
    log_tool_output(output=outputs, tool_name=import_git_repo.__name__)

    return ctx.repo.workdir


@register_tool(tags=["software development", "Clone a git repository to local"])
async def git_clone(url: Union[str, Path], output_dir: Union[str, Path] = None) -> Path:
    """
    Clones a Git repository from the given URL.

    Args:
        url (Union[str, Path]): The URL or local path of the Git repository to clone.
        output_dir (Union[str, Path], optional): The directory where the repository should be cloned.
            If None, the repository will be cloned into the current working directory. Defaults to None.

    Returns:
        Path: The path to the cloned repository.

    Example:
        >>> url = "https://github.com/iorisa/snake-game.git"
        >>> local_path = await git_clone(url=url)
        >>> print(local_path)
        /local/path/to/snake-game
    """
    repo = await GitRepository.clone_from(url=url, output_dir=output_dir)
    return repo.workdir


@register_tool(tags=["software development", "Commit the changes and push to remote git repository."])
async def git_push(
    local_path: Union[str, Path],
    access_token: str,
    comments: str = "Commit",
    new_branch: str = "",
) -> GitBranch:
    """
    Pushes changes from a local Git repository to its remote counterpart.

    Args:
        local_path (Union[str, Path]): The path to the local Git repository.
        access_token (str): The access token for authentication. Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`, `https://github.com/PyGithub/PyGithub/blob/main/doc/examples/Authentication.rst`.
        comments (str, optional): The commit message to use. Defaults to "Commit".
        new_branch (str, optional): The name of the new branch to create and push changes to.
            If not provided, changes will be pushed to the current branch. Defaults to "".

    Returns:
        GitBranch: The branch to which the changes were pushed.
    Raises:
        ValueError: If the provided local_path does not point to a valid Git repository.

    Example:
        >>> url = "https://github.com/iorisa/snake-game.git"
        >>> local_path = await git_clone(url=url)
        >>> access_token = await get_env(key="access_token", app_name="github")  # Read access token from enviroment variables.
        >>> comments = "Archive"
        >>> new_branch = "feature/new"
        >>> branch = await git_push(local_path=local_path, access_token=access_token, comments=comments, new_branch=new_branch)
        >>> base = branch.base
        >>> head = branch.head
        >>> repo_name = branch.repo_name
        >>> print(f"base branch:'{base}', head branch:'{head}', repo_name:'{repo_name}'")
        base branch:'master', head branch:'feature/new', repo_name:'iorisa/snake-game'

    """
    if not GitRepository.is_git_dir(local_path):
        raise ValueError("Invalid local git repository")

    repo = GitRepository(local_path=local_path, auto_init=False)
    branch = await repo.push(new_branch=new_branch, comments=comments, access_token=access_token)
    return branch


@register_tool(tags=["software development", "create a git pull/merge request"])
async def git_create_pull(
    base: str,
    head: str,
    base_repo_name: str,
    access_token: str,
    head_repo_name: Optional[str] = None,
    title: Optional[str] = None,
    body: Optional[str] = None,
    issue: Optional[Issue] = None,
) -> PullRequest:
    """
    Creates a pull request on a Git repository.

    Args:
        base (str): The base branch of the pull request.
        head (str): The head branch of the pull request.
        base_repo_name (str): The full repository name (user/repo) where the pull request will be created.
        access_token (str): The access token for authentication. Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`, `https://github.com/PyGithub/PyGithub/blob/main/doc/examples/Authentication.rst`.
        head_repo_name (Optional[str], optional): The full repository name (user/repo) where the pull request will merge from. Defaults to None.
        title (Optional[str], optional): The title of the pull request. Defaults to None.
        body (Optional[str], optional): The body of the pull request. Defaults to None.
        issue (Optional[Issue], optional): The related issue of the pull request. Defaults to None.

    Example:
        >>> # push and create pull
        >>> url = "https://github.com/iorisa/snake-game.git"
        >>> local_path = await git_clone(url=url)
        >>> access_token = await get_env(key="access_token", app_name="github") # Read access token from enviroment variables.
        >>> comments = "Archive"
        >>> new_branch = "feature/new"
        >>> branch = await git_push(local_path=local_path, access_token=access_token, comments=comments, new_branch=new_branch)
        >>> base = branch.base
        >>> head = branch.head
        >>> repo_name = branch.repo_name
        >>> print(f"base branch:'{base}', head branch:'{head}', repo_name:'{repo_name}'")
        base branch:'master', head branch:'feature/new', repo_name:'iorisa/snake-game'
        >>> title = "feat: modify http lib",
        >>> body = "Change HTTP library used to send requests"
        >>> pr = await git_create_pull(
        >>>   base_repo_name=repo_name,
        >>>   base=base,
        >>>   head=head,
        >>>   title=title,
        >>>   body=body,
        >>>   access_token=access_token,
        >>> )
        >>> print(pr)
        PullRequest("feat: modify http lib")

        >>> # create pull request
        >>> base_repo_name = "geekan/MetaGPT"
        >>> head_repo_name = "ioris/MetaGPT"
        >>> base = "master"
        >>> head = "feature/http"
        >>> title = "feat: modify http lib",
        >>> body = "Change HTTP library used to send requests"
        >>> access_token = await get_env(key="access_token", app_name="github")  # Read access token from enviroment variables.
        >>> pr = await git_create_pull(
        >>>   base_repo_name=base_repo_name,
        >>>   head_repo_name=head_repo_name,
        >>>   base=base,
        >>>   head=head,
        >>>   title=title,
        >>>   body=body,
        >>>   access_token=access_token,
        >>> )
        >>> print(pr)
        PullRequest("feat: modify http lib")


    Returns:
        PullRequest: The created pull request.
    """
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
        access_token (str): The access token for authentication.
        body (Optional[str], optional): The body of the issue. Defaults to None.

    Example:
        >>> repo_name = "geekan/MetaGPT"
        >>> title = "This is a new issue"
        >>> access_token = await get_env(key="access_token", app_name="github")  # Read access token from enviroment variables.
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
    return await GitRepository.create_issue(repo_name=repo_name, title=title, body=body, access_token=access_token)
