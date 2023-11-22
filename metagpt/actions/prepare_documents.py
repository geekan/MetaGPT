#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : git_repository.py
@Desc: PrepareDocuments Action: initialize project folder and add new requirements to docs/requirements.txt.
        RFC 135 2.2.3.5.1.
"""

from pathlib import Path

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.const import DOCS_FILE_REPO, REQUIREMENT_FILENAME, WORKSPACE_ROOT
from metagpt.schema import Document
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.git_repository import GitRepository


class PrepareDocuments(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, with_messages, **kwargs):
        if CONFIG.git_repo:
            docs_repo = CONFIG.git_repo.new_file_repository(DOCS_FILE_REPO)
            doc = await docs_repo.get(REQUIREMENT_FILENAME)
            return ActionOutput(content=doc.json(exclue="content"), instruct_content=doc)

        # Create and initialize the workspace folder, initialize the Git environment.
        CONFIG.git_repo = GitRepository()
        workdir = Path(CONFIG.WORKDIR) if CONFIG.WORKDIR else WORKSPACE_ROOT / FileRepository.new_file_name()
        CONFIG.git_repo.open(local_path=workdir, auto_init=True)

        # Write the newly added requirements from the main parameter idea to `docs/requirement.txt`.
        docs_file_repository = CONFIG.git_repo.new_file_repository(DOCS_FILE_REPO)
        doc = Document(root_path=DOCS_FILE_REPO, filename=REQUIREMENT_FILENAME, content=with_messages[0].content)
        await docs_file_repository.save(REQUIREMENT_FILENAME, content=doc.content)

        # Send a Message notification to the WritePRD action, instructing it to process requirements using
        # `docs/requirement.txt` and `docs/prds/`.
        return ActionOutput(content=doc.content, instruct_content=doc)
