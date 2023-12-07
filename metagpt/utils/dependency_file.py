#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/22
@Author  : mashenquan
@File    : dependency_file.py
@Desc: Implementation of the dependency file described in Section 2.2.3.2 of RFC 135.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Set

import aiofiles

from metagpt.config import CONFIG
from metagpt.logs import logger


class DependencyFile:
    """A class representing a DependencyFile for managing dependencies.

    :param workdir: The working directory path for the DependencyFile.
    """

    def __init__(self, workdir: Path | str):
        """Initialize a DependencyFile instance.

        :param workdir: The working directory path for the DependencyFile.
        """
        self._dependencies = {}
        self._filename = Path(workdir) / ".dependencies.json"

    async def load(self):
        """Load dependencies from the file asynchronously."""
        if not self._filename.exists():
            return
        try:
            async with aiofiles.open(str(self._filename), mode="r") as reader:
                data = await reader.read()
            self._dependencies = json.loads(data)
        except Exception as e:
            logger.error(f"Failed to load {str(self._filename)}, error:{e}")

    async def save(self):
        """Save dependencies to the file asynchronously."""
        try:
            data = json.dumps(self._dependencies)
            async with aiofiles.open(str(self._filename), mode="w") as writer:
                await writer.write(data)
        except Exception as e:
            logger.error(f"Failed to save {str(self._filename)}, error:{e}")

    async def update(self, filename: Path | str, dependencies: Set[Path | str], persist=True):
        """Update dependencies for a file asynchronously.

        :param filename: The filename or path.
        :param dependencies: The set of dependencies.
        :param persist: Whether to persist the changes immediately.
        """
        if persist:
            await self.load()

        root = self._filename.parent
        try:
            key = Path(filename).relative_to(root)
        except ValueError:
            key = filename

        if dependencies:
            relative_paths = []
            for i in dependencies:
                try:
                    relative_paths.append(str(Path(i).relative_to(root)))
                except ValueError:
                    relative_paths.append(str(i))
            self._dependencies[str(key)] = relative_paths
        elif str(key) in self._dependencies:
            del self._dependencies[str(key)]

        if persist:
            await self.save()

    async def get(self, filename: Path | str, persist=True):
        """Get dependencies for a file asynchronously.

        :param filename: The filename or path.
        :param persist: Whether to load dependencies from the file immediately.
        :return: A set of dependencies.
        """
        if persist:
            await self.load()

        root = CONFIG.git_repo.workdir
        try:
            key = Path(filename).relative_to(root)
        except ValueError:
            key = filename
        return set(self._dependencies.get(str(key), {}))

    def delete_file(self):
        """Delete the dependency file."""
        self._filename.unlink(missing_ok=True)

    @property
    def exists(self):
        """Check if the dependency file exists."""
        return self._filename.exists()
