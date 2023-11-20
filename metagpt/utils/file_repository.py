#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : git_repository.py
@Desc: File repository management. RFC 135 2.2.3.2, 2.2.3.4 and 2.2.3.13.
"""
import json
from pathlib import Path
from typing import Dict, List

import aiofiles

from metagpt.utils.git_repository import GitRepository


class FileRepository:
    def __init__(self, git_repo: GitRepository, relative_path: Path = "."):
        self._relative_path = relative_path  # Relative path based on the Git repository.
        self._git_repo = git_repo
        self._dependencies: Dict[str, List[str]] = {}

    async def save(self, filename: Path, content, dependencies: List[str] = None):
        path_name = self.workdir / filename
        with aiofiles.open(str(path_name), mode="w") as writer:
            await writer.write(content)
        if dependencies is not None:
            await self.update_dependency(filename, dependencies)

    async def update_dependency(self, filename, dependencies: List[str]):
        self._dependencies[str(filename)] = dependencies

    async def save_dependency(self):
        filename = ".dependencies.json"
        path_name = self.workdir / filename
        data = json.dumps(self._dependencies)
        with aiofiles.open(str(path_name), mode="w") as writer:
            await writer.write(data)

    @property
    def workdir(self):
        return self._git_repo.workdir / self._relative_path
