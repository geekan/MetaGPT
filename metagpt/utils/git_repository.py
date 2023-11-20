#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : git_repository.py
@Desc: Git repository management
"""
from __future__ import annotations

import shutil
from enum import Enum
from pathlib import Path
from typing import Dict

from git.repo import Repo
from git.repo.fun import is_git_dir

from metagpt.const import WORKSPACE_ROOT


class ChangeType(Enum):
    ADDED = "A"  # File was added
    COPIED = "C"  # File was copied
    DELETED = "D"  # File was deleted
    RENAMED = "R"  # File was renamed
    MODIFIED = "M"  # File was modified
    TYPE_CHANGED = "T"  # Type of the file was changed
    UNTRACTED = "U"  # File is untracked (not added to version control)


class GitRepository:
    def __init__(self, local_path=None, auto_init=True):
        self._repository = None
        if local_path:
            self.open(local_path=local_path, auto_init=auto_init)

    def open(self, local_path: Path, auto_init=False):
        if self.is_git_dir(local_path):
            self._repository = Repo(local_path)
            return
        if not auto_init:
            return
        local_path.mkdir(parents=True, exist_ok=True)
        return self._init(local_path)

    def _init(self, local_path: Path):
        self._repository = Repo.init(path=local_path)

    def add_change(self, files: Dict):
        if not self.is_valid or not files:
            return

        for k, v in files.items():
            self._repository.index.remove(k) if v is ChangeType.DELETED else self._repository.index.add([k])

    def commit(self, comments):
        if self.is_valid:
            self._repository.index.commit(comments)

    def delete_repository(self):
        # Delete the repository directory
        if self.is_valid:
            shutil.rmtree(self._repository.working_dir)

    @property
    def changed_files(self) -> Dict[str, str]:
        files = {i: ChangeType.UNTRACTED for i in self._repository.untracked_files}
        changed_files = {f.a_path: ChangeType(f.change_type) for f in self._repository.index.diff(None)}
        files.update(changed_files)
        return files

    @staticmethod
    def is_git_dir(local_path):
        git_dir = local_path / ".git"
        if git_dir.exists() and is_git_dir(git_dir):
            return True
        return False

    @property
    def is_valid(self):
        return bool(self._repository)

    @property
    def status(self) -> str:
        if not self.is_valid:
            return ""
        return self._repository.git.status()

    @property
    def workdir(self) -> Path | None:
        if not self.is_valid:
            return None
        return Path(self._repository.working_dir)


if __name__ == "__main__":
    path = WORKSPACE_ROOT / "git"
    path.mkdir(exist_ok=True, parents=True)

    repo = GitRepository()
    repo.open(path, auto_init=True)

    changes = repo.changed_files
    print(changes)
    repo.add_change(changes)
    print(repo.status)
    repo.commit("test")
    print(repo.status)
    repo.delete_repository()
