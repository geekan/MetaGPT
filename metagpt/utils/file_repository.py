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
        """Initialize a FileRepository instance.

        :param git_repo: The associated GitRepository instance.
        :param relative_path: The relative path within the Git repository.
        """
        self._relative_path = relative_path
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
        """Save content to a file and update its dependencies.

        :param filename: The filename or path within the repository.
        :param content: The content to be saved.
        :param dependencies: List of dependency filenames or paths.
        """
        path_name = self.workdir / filename
        path_name.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(str(path_name), mode="w") as writer:
            await writer.write(content)
        if dependencies is not None:
            await self.update_dependency(filename, dependencies)

    async def get(self, filename: Path | str):
        """Read the content of a file.

        :param filename: The filename or path within the repository.
        :return: The content of the file.
        """
        path_name = self.workdir / filename
        async with aiofiles.open(str(path_name), mode="r") as reader:
            return await reader.read()

    def get_dependency(self, filename: Path | str) -> List:
        """Get the dependencies of a file.

        :param filename: The filename or path within the repository.
        :return: List of dependency filenames or paths.
        """
        key = str(filename)
        return self._dependencies.get(key, [])

    def get_changed_dependency(self, filename: Path | str) -> List:
        """Get the dependencies of a file that have changed.

        :param filename: The filename or path within the repository.
        :return: List of changed dependency filenames or paths.
        """
        dependencies = self.get_dependency(filename=filename)
        changed_files = self.changed_files
        changed_dependent_files = []
        for df in dependencies:
            if df in changed_files.keys():
                changed_dependent_files.append(df)
        return changed_dependent_files

    async def update_dependency(self, filename, dependencies: List[str]):
        """Update the dependencies of a file.

        :param filename: The filename or path within the repository.
        :param dependencies: List of dependency filenames or paths.
        """
        self._dependencies[str(filename)] = dependencies

    async def save_dependency(self):
        """Save the dependencies to a file."""
        data = json.dumps(self._dependencies)
        with aiofiles.open(str(self.dependency_path_name), mode="w") as writer:
            await writer.write(data)

    @property
    def workdir(self):
        """Return the absolute path to the working directory of the FileRepository.

        :return: The absolute path to the working directory.
        """
        return self._git_repo.workdir / self._relative_path

    @property
    def dependency_path_name(self):
        """Return the absolute path to the dependency file.

        :return: The absolute path to the dependency file.
        """
        filename = ".dependencies.json"
        path_name = self.workdir / filename
        return path_name

    @property
    def changed_files(self) -> Dict[str, str]:
        """Return a dictionary of changed files and their change types.

        :return: A dictionary where keys are file paths and values are change types.
        """
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
        """Get the files in a directory that have changed.

        :param dir: The directory path within the repository.
        :return: List of changed filenames or paths within the directory.
        """
        changed_files = self.changed_files
        children = []
        for f in changed_files:
            try:
                Path(f).relative_to(Path(dir))
            except ValueError:
                continue
            children.append(str(f))
        return children
