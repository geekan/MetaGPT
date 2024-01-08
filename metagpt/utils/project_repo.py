#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/8
@Author  : mashenquan
@File    : project_repo.py
@Desc    : Wrapper for GitRepository and FileRepository of project.
    Implementation of Chapter 4.6 of https://deepwisdom.feishu.cn/wiki/CUK4wImd7id9WlkQBNscIe9cnqh
"""
from __future__ import annotations

from pathlib import Path

from metagpt.const import (
    CLASS_VIEW_FILE_REPO,
    CODE_SUMMARIES_FILE_REPO,
    CODE_SUMMARIES_PDF_FILE_REPO,
    COMPETITIVE_ANALYSIS_FILE_REPO,
    DATA_API_DESIGN_FILE_REPO,
    GRAPH_REPO_FILE_REPO,
    PRD_PDF_FILE_REPO,
    PRDS_FILE_REPO,
    SD_OUTPUT_FILE_REPO,
    SEQ_FLOW_FILE_REPO,
    SYSTEM_DESIGN_FILE_REPO,
    SYSTEM_DESIGN_PDF_FILE_REPO,
    TASK_FILE_REPO,
    TASK_PDF_FILE_REPO,
    TEST_CODES_FILE_REPO,
    TEST_OUTPUTS_FILE_REPO,
)
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.git_repository import GitRepository


class DocFileRepositories:
    prd: FileRepository
    system_design: FileRepository
    task: FileRepository
    code_summary: FileRepository
    graph_repo: FileRepository
    class_view: FileRepository

    def __init__(self, git_repo):
        self.prd = git_repo.new_file_repository(relative_path=PRDS_FILE_REPO)
        self.system_design = git_repo.new_file_repository(relative_path=SYSTEM_DESIGN_FILE_REPO)
        self.task = git_repo.new_file_repository(relative_path=TASK_FILE_REPO)
        self.code_summary = git_repo.new_file_repository(relative_path=CODE_SUMMARIES_FILE_REPO)
        self.graph_repo = git_repo.new_file_repository(relative_path=GRAPH_REPO_FILE_REPO)
        self.class_view = git_repo.new_file_repository(relative_path=CLASS_VIEW_FILE_REPO)


class ResourceFileRepositories:
    competitive_analysis: FileRepository
    data_api_design: FileRepository
    seq_flow: FileRepository
    system_design: FileRepository
    prd: FileRepository
    api_spec_and_task: FileRepository
    code_summary: FileRepository
    sd_output: FileRepository

    def __init__(self, git_repo):
        self.competitive_analysis = git_repo.new_file_repository(relative_path=COMPETITIVE_ANALYSIS_FILE_REPO)
        self.data_api_design = git_repo.new_file_repository(relative_path=DATA_API_DESIGN_FILE_REPO)
        self.seq_flow = git_repo.new_file_repository(relative_path=SEQ_FLOW_FILE_REPO)
        self.system_design = git_repo.new_file_repository(relative_path=SYSTEM_DESIGN_PDF_FILE_REPO)
        self.prd = git_repo.new_file_repository(relative_path=PRD_PDF_FILE_REPO)
        self.api_spec_and_task = git_repo.new_file_repository(relative_path=TASK_PDF_FILE_REPO)
        self.code_summary = git_repo.new_file_repository(relative_path=CODE_SUMMARIES_PDF_FILE_REPO)
        self.sd_output = git_repo.new_file_repository(relative_path=SD_OUTPUT_FILE_REPO)


class ProjectRepo(FileRepository):
    def __init__(self, root: str | Path):
        git_repo = GitRepository(local_path=Path(root))
        super().__init__(git_repo=git_repo, relative_path=Path("."))

        self._git_repo = git_repo
        self.docs = DocFileRepositories(self._git_repo)
        self.resources = ResourceFileRepositories(self._git_repo)
        self.tests = self._git_repo.new_file_repository(relative_path=TEST_CODES_FILE_REPO)
        self.test_outputs = self._git_repo.new_file_repository(relative_path=TEST_OUTPUTS_FILE_REPO)

    @property
    def git_repo(self):
        return self._git_repo
