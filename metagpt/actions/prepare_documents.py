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
from metagpt.config import CONFIG
from metagpt.const import DOCS_FILE_REPO, REQUIREMENT_FILENAME
from metagpt.schema import Document
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.git_repository import GitRepository


class PrepareDocuments(Action):
    """PrepareDocuments Action: initialize project folder and add new requirements to docs/requirements.txt."""

    name: str = "PrepareDocuments"
    context: Optional[str] = None

    def _init_repo(self):
        """Initialize the Git environment."""
        if not CONFIG.project_path:
            name = CONFIG.project_name or FileRepository.new_filename()
            path = Path(CONFIG.workspace_path) / name
        else:
            path = Path(CONFIG.project_path)
        if path.exists() and not CONFIG.inc:
            shutil.rmtree(path)
        CONFIG.project_path = path
        CONFIG.git_repo = GitRepository(local_path=path, auto_init=True)

    async def run(self, with_messages, **kwargs):
        """Create and initialize the workspace folder, initialize the Git environment."""
        self._init_repo()

        # Write the newly added requirements from the main parameter idea to `docs/requirement.txt`.
        doc = Document(root_path=DOCS_FILE_REPO, filename=REQUIREMENT_FILENAME, content=with_messages[0].content)
        await FileRepository.save_file(filename=REQUIREMENT_FILENAME, content=doc.content, relative_path=DOCS_FILE_REPO)

        # Send a Message notification to the WritePRD action, instructing it to process requirements using
        # `docs/requirement.txt` and `docs/prds/`.
        return ActionOutput(content=doc.content, instruct_content=doc)
