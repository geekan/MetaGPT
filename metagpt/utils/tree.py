#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/3/11
@Author  : mashenquan
@File    : tree.py
@Desc    : Implement the same functionality as the `tree` command.
Example:
        root
        +-- dir1
        |   +-- file1.txt
        |   +-- file2.txt
        +-- dir2
        |   +-- subdir1
        |   |   +-- file1.txt
        |   |   +-- file2.txt
        |   +-- subdir2
        |       +-- file1.txt
        |       +-- file2.txt
        +-- file.txt
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List

from anthropic import BaseModel
from pydantic import Field


class Tree(BaseModel):
    """
    Represents a directory tree structure.

    Attributes:
        root (str): The root directory of the tree.
        tree (Dict[str, Dict]): The tree structure as a dictionary.

    Methods:
        print: Print the directory tree structure.

    """

    root: str
    tree: Dict[str, Dict] = Field(default_factory=dict)

    def print(self, git_ignore_rules: Callable = None) -> str:
        """
        Recursively traverses the directory structure and prints it out in a tree-like format.

        Args:
            git_ignore_rules (Callable): Optional. A function to filter files to ignore.

        Returns:
            str: A string representation of the directory tree.

        """
        root = Path(self.root).resolve()
        self.tree[root.name] = self._list_children(root=root, git_ignore_rules=git_ignore_rules)
        v = self._print_tree(self.tree)
        return "\n".join(v)

    @staticmethod
    def _list_children(root: Path, git_ignore_rules: Callable) -> Dict[str, Dict]:
        tree = {}
        for i in root.iterdir():
            if git_ignore_rules and git_ignore_rules(str(i)):
                continue
            if i.is_file():
                tree[i.name] = {}
            else:
                tree[i.name] = Tree._list_children(root=i, git_ignore_rules=git_ignore_rules)
        return tree

    @staticmethod
    def _print_tree(tree: Dict[str:Dict], indent: int = 0) -> List[str]:
        ret = []
        for name, children in tree.items():
            ret.append(name)
            if not children:
                continue
            lines = Tree._print_tree(tree=children, indent=indent + 1)
            for j, v in enumerate(lines):
                if v[0] not in ["+", " ", "|"]:
                    ret = Tree._add_line(ret)
                    row = f"+-- {v}"
                else:
                    row = f"    {v}"
                ret.append(row)
        return ret

    @staticmethod
    def _add_line(rows: List[str]) -> List[str]:
        for i in range(len(rows) - 1, -1, -1):
            v = rows[i]
            if v[0] != " ":
                return rows
            rows[i] = "|" + v[1:]
        return rows
