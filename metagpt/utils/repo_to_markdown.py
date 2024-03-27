#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file provides functionality to convert a local repository into a markdown representation.
"""
from __future__ import annotations

import mimetypes
from pathlib import Path

from gitignore_parser import parse_gitignore

from metagpt.logs import logger
from metagpt.utils.common import aread, awrite, get_markdown_codeblock_type, list_files
from metagpt.utils.tree import tree


async def repo_to_markdown(repo_path: str | Path, output: str | Path = None, gitignore: str | Path = None) -> str:
    """
    Convert a local repository into a markdown representation.

    This function takes a path to a local repository and generates a markdown representation of the repository structure,
    including directory trees and file listings.

    Args:
        repo_path (str | Path): The path to the local repository.
        output (str | Path, optional): The path to save the generated markdown file. Defaults to None.
        gitignore (str | Path, optional): The path to the .gitignore file. Defaults to None.

    Returns:
        str: The markdown representation of the repository.
    """
    repo_path = Path(repo_path)
    gitignore = Path(gitignore or Path(__file__).parent / "../../.gitignore").resolve()

    markdown = await _write_dir_tree(repo_path=repo_path, gitignore=gitignore)

    gitignore_rules = parse_gitignore(full_path=str(gitignore))
    markdown += await _write_files(repo_path=repo_path, gitignore_rules=gitignore_rules)

    if output:
        await awrite(filename=str(output), data=markdown, encoding="utf-8")
    return markdown


async def _write_dir_tree(repo_path: Path, gitignore: Path) -> str:
    try:
        content = tree(repo_path, gitignore, run_command=True)
    except Exception as e:
        logger.info(f"{e}, using safe mode.")
        content = tree(repo_path, gitignore, run_command=False)

    doc = f"## Directory Tree\n```text\n{content}\n```\n---\n\n"
    return doc


async def _write_files(repo_path, gitignore_rules) -> str:
    filenames = list_files(repo_path)
    markdown = ""
    for filename in filenames:
        if gitignore_rules(str(filename)):
            continue
        markdown += await _write_file(filename=filename, repo_path=repo_path)
    return markdown


async def _write_file(filename: Path, repo_path: Path) -> str:
    relative_path = filename.relative_to(repo_path)
    markdown = f"## {relative_path}\n"

    mime_type, _ = mimetypes.guess_type(filename.name)
    if "text/" not in mime_type:
        logger.info(f"Ignore content: {filename}")
        markdown += "<binary file>\n---\n\n"
        return markdown
    content = await aread(filename, encoding="utf-8")
    content = content.replace("```", "\\`\\`\\`").replace("---", "\\-\\-\\-")
    code_block_type = get_markdown_codeblock_type(filename.name)
    markdown += f"```{code_block_type}\n{content}\n```\n---\n\n"
    return markdown
