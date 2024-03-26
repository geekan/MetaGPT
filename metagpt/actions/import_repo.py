#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List

from metagpt.actions import Action
from metagpt.schema import Message
from metagpt.tools.libs.git import git_clone
from metagpt.utils.git_repository import GitRepository
from metagpt.utils.project_repo import ProjectRepo


class ImportRepo(Action):
    repo_path: str

    async def run(self, with_messages: List[Message] = None, **kwargs) -> Message:
        await self._create_repo()
        pass

    async def _create_repo(self):
        path = await git_clone(url=self.repo_path, output_dir=self.config.workspace.path)
        self.repo_path = str(path)
        self.config.project_path = path
        self.context.git_repo = GitRepository(local_path=path, auto_init=True)
        self.context.repo = ProjectRepo(self.context.git_repo)
