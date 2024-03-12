#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/3/11
@Author  : mashenquan
@File    : tree.py
@Desc    : Implement the same functionality as the `tree` command.
        Example:
            >>> print_tree(".")
            utils
            +-- serialize.py
            +-- project_repo.py
            +-- tree.py
            +-- mmdc_playwright.py
            +-- cost_manager.py
            +-- __pycache__
            |   +-- __init__.cpython-39.pyc
            |   +-- redis.cpython-39.pyc
            |   +-- singleton.cpython-39.pyc
            |   +-- embedding.cpython-39.pyc
            |   +-- make_sk_kernel.cpython-39.pyc
            |   +-- file_repository.cpython-39.pyc
            +-- file.py
            +-- save_code.py
            +-- common.py
            +-- redis.py
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List


def tree(root: str | Path, git_ignore_rules: Callable = None) -> str:
    """
    Recursively traverses the directory structure and prints it out in a tree-like format.

    Args:
        root (str or Path): The root directory from which to start traversing.
        git_ignore_rules (Callable): Optional. A function to filter files to ignore.

    Returns:
        str: A string representation of the directory tree.

    Example:
            >>> tree(".")
            utils
            +-- serialize.py
            +-- project_repo.py
            +-- tree.py
            +-- mmdc_playwright.py
            +-- __pycache__
            |   +-- __init__.cpython-39.pyc
            |   +-- redis.cpython-39.pyc
            |   +-- singleton.cpython-39.pyc
            +-- parse_docstring.py

            >>> from gitignore_parser import parse_gitignore
            >>> tree(".", git_ignore_rules=parse_gitignore(full_path="../../.gitignore"))
            utils
            +-- serialize.py
            +-- project_repo.py
            +-- tree.py
            +-- mmdc_playwright.py
            +-- parse_docstring.py

    """
    root = Path(root).resolve()
    dir_ = {root.name: _list_children(root=root, git_ignore_rules=git_ignore_rules)}
    v = _print_tree(dir_)
    return "\n".join(v)


def _list_children(root: Path, git_ignore_rules: Callable) -> Dict[str, Dict]:
    dir_ = {}
    for i in root.iterdir():
        if git_ignore_rules and git_ignore_rules(str(i)):
            continue
        try:
            if i.is_file():
                dir_[i.name] = {}
            else:
                dir_[i.name] = _list_children(root=i, git_ignore_rules=git_ignore_rules)
        except (FileNotFoundError, PermissionError, OSError):
            dir_[i.name] = {}
    return dir_


def _print_tree(dir_: Dict[str:Dict]) -> List[str]:
    ret = []
    for name, children in dir_.items():
        ret.append(name)
        if not children:
            continue
        lines = _print_tree(children)
        for j, v in enumerate(lines):
            if v[0] not in ["+", " ", "|"]:
                ret = _add_line(ret)
                row = f"+-- {v}"
            else:
                row = f"    {v}"
            ret.append(row)
    return ret


def _add_line(rows: List[str]) -> List[str]:
    for i in range(len(rows) - 1, -1, -1):
        v = rows[i]
        if v[0] != " ":
            return rows
        rows[i] = "|" + v[1:]
    return rows
