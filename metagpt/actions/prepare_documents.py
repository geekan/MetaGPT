#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : prepare_documents.py
@Desc: PrepareDocuments Action: initialize project folder and add new requirements to docs/requirements.txt.
        RFC 135 2.2.3.5.1.
"""
import shutil
from pathlib import Path
from typing import Optional

from metagpt.actions import Action, ActionOutput
from metagpt.const import DOCS_FILE_REPO, REQUIREMENT_FILENAME
from metagpt.schema import Document
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.git_repository import GitRepository


class PrepareDocuments(Action):
    """PrepareDocuments Action: initialize project folder and add new requirements to docs/requirements.txt."""

    name: str = "PrepareDocuments"
    context: Optional[str] = None

    @property
    def config(self):
        return self.g_context.config

    def _init_repo(self):
        """Initialize the Git environment."""
        if not self.config.project_path:
            name = self.config.project_name or FileRepository.new_filename()
            path = Path(self.config.workspace.path) / name
        else:
            path = Path(self.config.project_path)
        if path.exists() and not self.config.inc:
            shutil.rmtree(path)
        self.config.project_path = path
        self.config.project_name = path.name
        self.g_context.git_repo = GitRepository(local_path=path, auto_init=True)

    async def run(self, with_messages, **kwargs):
        """Create and initialize the workspace folder, initialize the Git environment."""
        self._init_repo()

        # Write the newly added requirements from the main parameter idea to `docs/requirement.txt`.
        doc = Document(root_path=DOCS_FILE_REPO, filename=REQUIREMENT_FILENAME, content=with_messages[0].content)
        await FileRepository.save_file(filename=REQUIREMENT_FILENAME, content=doc.content, relative_path=DOCS_FILE_REPO)

        # Send a Message notification to the WritePRD action, instructing it to process requirements using
        # `docs/requirement.txt` and `docs/prds/`.
        return ActionOutput(content=doc.content, instruct_content=doc)
