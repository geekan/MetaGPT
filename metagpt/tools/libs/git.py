#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

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
