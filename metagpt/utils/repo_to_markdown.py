#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file provides functionality to convert a local repository into a markdown representation.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Tuple, Union

from gitignore_parser import parse_gitignore

from metagpt.logs import logger
from metagpt.utils.common import (
    aread,
    awrite,
    get_markdown_codeblock_type,
    get_mime_type,
    list_files,
)
from metagpt.utils.tree import tree


async def repo_to_markdown(repo_path: str | Path, output: str | Path = None) -> str:
    """
    Convert a local repository into a markdown representation.

    This function takes a path to a local repository and generates a markdown representation of the repository structure,
    including directory trees and file listings.

    Args:
        repo_path (str | Path): The path to the local repository.
        output (str | Path, optional): The path to save the generated markdown file. Defaults to None.

    Returns:
        str: The markdown representation of the repository.
    """
    repo_path = Path(repo_path).resolve()
    gitignore_file = repo_path / ".gitignore"

    markdown = await _write_dir_tree(repo_path=repo_path, gitignore=gitignore_file)

    gitignore_rules = parse_gitignore(full_path=str(gitignore_file)) if gitignore_file.exists() else None
    markdown += await _write_files(repo_path=repo_path, gitignore_rules=gitignore_rules)

    if output:
        output_file = Path(output).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        await awrite(filename=str(output_file), data=markdown, encoding="utf-8")
        logger.info(f"save: {output_file}")
    return markdown


async def _write_dir_tree(repo_path: Path, gitignore: Path) -> str:
    try:
        content = await tree(repo_path, gitignore, run_command=True)
    except Exception as e:
        logger.info(f"{e}, using safe mode.")
        content = await tree(repo_path, gitignore, run_command=False)

    doc = f"## Directory Tree\n```text\n{content}\n```\n---\n\n"
    return doc


async def _write_files(repo_path, gitignore_rules=None) -> str:
    filenames = list_files(repo_path)
    markdown = ""
    pattern = r"^\..*"  # Hidden folders/files
    for filename in filenames:
        if gitignore_rules and gitignore_rules(str(filename)):
            continue
        ignore = False
        for i in filename.parts:
            if re.match(pattern, i):
                ignore = True
                break
        if ignore:
            continue
        markdown += await _write_file(filename=filename, repo_path=repo_path)
    return markdown


async def _write_file(filename: Path, repo_path: Path) -> str:
    is_text, mime_type = await is_text_file(filename)
    if not is_text:
        logger.info(f"Ignore content: {filename}")
        return ""

    try:
        relative_path = filename.relative_to(repo_path)
        markdown = f"## {relative_path}\n"
        content = await aread(filename, encoding="utf-8")
        content = content.replace("```", "\\`\\`\\`").replace("---", "\\-\\-\\-")
        code_block_type = get_markdown_codeblock_type(filename.name)
        markdown += f"```{code_block_type}\n{content}\n```\n---\n\n"
        return markdown
    except Exception as e:
        logger.error(e)
        return ""


async def is_text_file(filename: Union[str, Path]) -> Tuple[bool, str]:
    """
    Determines if the specified file is a text file based on its MIME type.

    Args:
        filename (Union[str, Path]): The path to the file.

    Returns:
        Tuple[bool, str]: A tuple where the first element indicates if the file is a text file
        (True for text file, False otherwise), and the second element is the MIME type of the file.
    """
    pass_set = {
        "application/json",
        "application/vnd.chipnuts.karaoke-mmd",
        "application/javascript",
        "application/xml",
        "application/x-sh",
        "application/sql",
    }
    denied_set = {
        "application/zlib",
        "application/octet-stream",
        "image/svg+xml",
        "application/pdf",
        "application/msword",
        "application/vnd.ms-excel",
        "audio/x-wav",
        "application/x-git",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "image/jpeg",
        "audio/mpeg",
        "video/mp2t",
        "inode/x-empty",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "image/png",
        "image/vnd.microsoft.icon",
        "video/mp4",
    }
    mime_type = await get_mime_type(Path(filename), force_read=True)
    v = "text/" in mime_type or mime_type in pass_set
    if v:
        return True, mime_type

    if mime_type not in denied_set:
        logger.info(mime_type)
    return False, mime_type
