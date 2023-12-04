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

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.const import DEFAULT_WORKSPACE_ROOT, DOCS_FILE_REPO, REQUIREMENT_FILENAME
from metagpt.schema import Document
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.git_repository import GitRepository


class PrepareDocuments(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, with_messages, **kwargs):
        if not CONFIG.git_repo:
            # Create and initialize the workspace folder, initialize the Git environment.
            project_name = CONFIG.project_name or FileRepository.new_filename()
            workdir = Path(CONFIG.project_path or DEFAULT_WORKSPACE_ROOT / project_name)
            if not CONFIG.inc and workdir.exists():
                shutil.rmtree(workdir)
            CONFIG.git_repo = GitRepository()
            CONFIG.git_repo.open(local_path=workdir, auto_init=True)

        # Write the newly added requirements from the main parameter idea to `docs/requirement.txt`.
        doc = Document(root_path=DOCS_FILE_REPO, filename=REQUIREMENT_FILENAME, content=with_messages[0].content)
        await FileRepository.save_file(filename=REQUIREMENT_FILENAME, content=doc.content, relative_path=DOCS_FILE_REPO)

        # Send a Message notification to the WritePRD action, instructing it to process requirements using
        # `docs/requirement.txt` and `docs/prds/`.
        return ActionOutput(content=doc.content, instruct_content=doc)
