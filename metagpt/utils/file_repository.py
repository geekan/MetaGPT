#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : git_repository.py
@Desc: File repository management. RFC 135 2.2.3.2, 2.2.3.4 and 2.2.3.13.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import aiofiles

from metagpt.logs import logger


class FileRepository:
    def __init__(self, git_repo, relative_path: Path = Path(".")):
        self._relative_path = relative_path  # Relative path based on the Git repository.
        self._git_repo = git_repo
        self._dependencies: Dict[str, List[str]] = {}

        # Initializing
        self.workdir.mkdir(parents=True, exist_ok=True)
        if self.dependency_path_name.exists():
            try:
                with open(str(self.dependency_path_name), mode="r") as reader:
                    self._dependencies = json.load(reader)
            except Exception as e:
                logger.error(f"Failed to load {str(self.dependency_path_name)}, error:{e}")

    async def save(self, filename: Path | str, content, dependencies: List[str] = None):
        path_name = self.workdir / filename
        path_name.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(str(path_name), mode="w") as writer:
            await writer.write(content)
        if dependencies is not None:
            await self.update_dependency(filename, dependencies)

    async def get(self, filename: Path | str):
        path_name = self.workdir / filename
        async with aiofiles.open(str(path_name), mode="r") as reader:
            return await reader.read()

    def get_dependency(self, filename: Path | str) -> List:
        key = str(filename)
        return self._dependencies.get(key, [])

    def get_changed_dependency(self, filename: Path | str) -> List:
        dependencies = self.get_dependency(filename=filename)
        changed_files = self.changed_files
        changed_dependent_files = []
        for df in dependencies:
            if df in changed_files.keys():
                changed_dependent_files.append(df)
        return changed_dependent_files

    async def update_dependency(self, filename, dependencies: List[str]):
        self._dependencies[str(filename)] = dependencies

    async def save_dependency(self):
        data = json.dumps(self._dependencies)
        with aiofiles.open(str(self.dependency_path_name), mode="w") as writer:
            await writer.write(data)

    @property
    def workdir(self):
        return self._git_repo.workdir / self._relative_path

    @property
    def dependency_path_name(self):
        filename = ".dependencies.json"
        path_name = self.workdir / filename
        return path_name

    @property
    def changed_files(self) -> Dict[str, str]:
        files = self._git_repo.changed_files
        relative_files = {}
        for p, ct in files.items():
            try:
                rf = Path(p).relative_to(self._relative_path)
            except ValueError:
                continue
            relative_files[str(rf)] = ct
        return relative_files

    def get_change_dir_files(self, dir: Path | str) -> List:
        changed_files = self.changed_files
        children = []
        for f in changed_files:
            try:
                Path(f).relative_to(Path(dir))
            except ValueError:
                continue
            children.append(str(f))
        return children
