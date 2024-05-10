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
from typing import Dict, Optional

from metagpt.actions import Action, UserRequirement
from metagpt.const import REQUIREMENT_FILENAME
from metagpt.logs import logger
from metagpt.schema import AIMessage
from metagpt.utils.common import any_to_str
from metagpt.utils.file_repository import FileRepository


class PrepareDocuments(Action):
    """PrepareDocuments Action: initialize project folder and add new requirements to docs/requirements.txt."""

    name: str = "PrepareDocuments"
    i_context: Optional[str] = None
    key_descriptions: Optional[Dict[str, str]] = None
    send_to: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.key_descriptions:
            self.key_descriptions = {"project_path": 'the project path if exists in "Original Requirement"'}

    @property
    def config(self):
        return self.context.config

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
        self.context.set_repo_dir(path)

    async def run(self, with_messages, **kwargs):
        """Create and initialize the workspace folder, initialize the Git environment."""
        user_requirements = [i for i in with_messages if i.cause_by == any_to_str(UserRequirement)]
        if not self.config.project_path and user_requirements and self.key_descriptions:
            args = await user_requirements[0].parse_resources(llm=self.llm, key_descriptions=self.key_descriptions)
            for k, v in args.items():
                if not v or k in ["resources", "reason"]:
                    continue
                self.context.kwargs.set(k, v)
                logger.info(f"{k}={v}")
            if self.context.kwargs.project_path:
                self.config.update_via_cli(
                    project_path=self.context.kwargs.project_path,
                    project_name="",
                    inc=False,
                    reqa_file=self.context.kwargs.reqa_file or "",
                    max_auto_summarize_code=0,
                )

        self._init_repo()

        # Write the newly added requirements from the main parameter idea to `docs/requirement.txt`.
        doc = await self.repo.docs.save(filename=REQUIREMENT_FILENAME, content=with_messages[0].content)
        # Send a Message notification to the WritePRD action, instructing it to process requirements using
        # `docs/requirement.txt` and `docs/prd/`.
        return AIMessage(content="", instruct_content=doc, cause_by=self, send_to=self.send_to)
