#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/8
# @Author  : mashenquan
# @File    : project_repo.py
# @Desc    : Wrapper for GitRepository and FileRepository of project.
#     Implementation of Chapter 4.6 of https://deepwisdom.feishu.cn/wiki/CUK4wImd7id9WlkQBNscIe9cnqh

from __future__ import annotations

from pathlib import Path

from metagpt.const import (
    CLASS_VIEW_FILE_REPO,
    CODE_PLAN_AND_CHANGE_FILE_REPO,
    CODE_PLAN_AND_CHANGE_PDF_FILE_REPO,
    CODE_SUMMARIES_FILE_REPO,
    CODE_SUMMARIES_PDF_FILE_REPO,
    COMPETITIVE_ANALYSIS_FILE_REPO,
    DATA_API_DESIGN_FILE_REPO,
    DOCS_FILE_REPO,
    GRAPH_REPO_FILE_REPO,
    PRD_PDF_FILE_REPO,
    PRDS_FILE_REPO,
    REQUIREMENT_FILENAME,
    RESOURCES_FILE_REPO,
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


class DocFileRepositories(FileRepository):
    """Represents repositories for documentation files within a project.

    Attributes:
        prd: A FileRepository for Product Requirement Documents.
        system_design: A FileRepository for system design documents.
        task: A FileRepository for task documents.
        code_summary: A FileRepository for code summary documents.
        graph_repo: A FileRepository for graph repository documents.
        class_view: A FileRepository for class view documents.
        code_plan_and_change: A FileRepository for code plan and change documents.
    """

    prd: FileRepository
    system_design: FileRepository
    task: FileRepository
    code_summary: FileRepository
    graph_repo: FileRepository
    class_view: FileRepository
    code_plan_and_change: FileRepository

    def __init__(self, git_repo):
        super().__init__(git_repo=git_repo, relative_path=DOCS_FILE_REPO)

        self.prd = git_repo.new_file_repository(relative_path=PRDS_FILE_REPO)
        self.system_design = git_repo.new_file_repository(relative_path=SYSTEM_DESIGN_FILE_REPO)
        self.task = git_repo.new_file_repository(relative_path=TASK_FILE_REPO)
        self.code_summary = git_repo.new_file_repository(relative_path=CODE_SUMMARIES_FILE_REPO)
        self.graph_repo = git_repo.new_file_repository(relative_path=GRAPH_REPO_FILE_REPO)
        self.class_view = git_repo.new_file_repository(relative_path=CLASS_VIEW_FILE_REPO)
        self.code_plan_and_change = git_repo.new_file_repository(relative_path=CODE_PLAN_AND_CHANGE_FILE_REPO)


class ResourceFileRepositories(FileRepository):
    """Represents repositories for resource files within a project.

    Attributes:
        competitive_analysis: A FileRepository for competitive analysis documents.
        data_api_design: A FileRepository for data API design documents.
        seq_flow: A FileRepository for sequence flow documents.
        system_design: A FileRepository for system design PDF documents.
        prd: A FileRepository for Product Requirement Document PDFs.
        api_spec_and_task: A FileRepository for API specification and task PDFs.
        code_summary: A FileRepository for code summary PDF documents.
        sd_output: A FileRepository for system design output files.
        code_plan_and_change: A FileRepository for code plan and change PDF documents.
    """

    competitive_analysis: FileRepository
    data_api_design: FileRepository
    seq_flow: FileRepository
    system_design: FileRepository
    prd: FileRepository
    api_spec_and_task: FileRepository
    code_summary: FileRepository
    sd_output: FileRepository
    code_plan_and_change: FileRepository

    def __init__(self, git_repo):
        super().__init__(git_repo=git_repo, relative_path=RESOURCES_FILE_REPO)

        self.competitive_analysis = git_repo.new_file_repository(relative_path=COMPETITIVE_ANALYSIS_FILE_REPO)
        self.data_api_design = git_repo.new_file_repository(relative_path=DATA_API_DESIGN_FILE_REPO)
        self.seq_flow = git_repo.new_file_repository(relative_path=SEQ_FLOW_FILE_REPO)
        self.system_design = git_repo.new_file_repository(relative_path=SYSTEM_DESIGN_PDF_FILE_REPO)
        self.prd = git_repo.new_file_repository(relative_path=PRD_PDF_FILE_REPO)
        self.api_spec_and_task = git_repo.new_file_repository(relative_path=TASK_PDF_FILE_REPO)
        self.code_summary = git_repo.new_file_repository(relative_path=CODE_SUMMARIES_PDF_FILE_REPO)
        self.sd_output = git_repo.new_file_repository(relative_path=SD_OUTPUT_FILE_REPO)
        self.code_plan_and_change = git_repo.new_file_repository(relative_path=CODE_PLAN_AND_CHANGE_PDF_FILE_REPO)


class ProjectRepo(FileRepository):
    """Represents the main project repository, including documentation, resources, and tests.

    Attributes:
        docs: A DocFileRepositories instance for accessing documentation files.
        resources: A ResourceFileRepositories instance for accessing resource files.
        tests: A FileRepository for test code files.
        test_outputs: A FileRepository for test output files.
        git_repo: The underlying GitRepository instance.
        workdir: The working directory of the git repository.
        srcs: A FileRepository for source code files, initialized by calling `with_src_path`.

    Raises:
        ValueError: If an invalid root is provided or if `srcs` is accessed before `with_src_path` is called.
    """

    def __init__(self, root: str | Path | GitRepository):
        if isinstance(root, str) or isinstance(root, Path):
            git_repo_ = GitRepository(local_path=Path(root))
        elif isinstance(root, GitRepository):
            git_repo_ = root
        else:
            raise ValueError("Invalid root")
        super().__init__(git_repo=git_repo_, relative_path=Path("."))
        self._git_repo = git_repo_
        self.docs = DocFileRepositories(self._git_repo)
        self.resources = ResourceFileRepositories(self._git_repo)
        self.tests = self._git_repo.new_file_repository(relative_path=TEST_CODES_FILE_REPO)
        self.test_outputs = self._git_repo.new_file_repository(relative_path=TEST_OUTPUTS_FILE_REPO)
        self._srcs_path = None

    @property
    async def requirement(self):
        return await self.docs.get(filename=REQUIREMENT_FILENAME)

    @property
    def git_repo(self) -> GitRepository:
        return self._git_repo

    @property
    def workdir(self) -> Path:
        return Path(self.git_repo.workdir)

    @property
    def srcs(self) -> FileRepository:
        if not self._srcs_path:
            raise ValueError("Call with_srcs first.")
        return self._git_repo.new_file_repository(self._srcs_path)

    def code_files_exists(self) -> bool:
        git_workdir = self.git_repo.workdir
        src_workdir = git_workdir / git_workdir.name
        if not src_workdir.exists():
            return False
        code_files = self.with_src_path(path=git_workdir / git_workdir.name).srcs.all_files
        if not code_files:
            return False

    def with_src_path(self, path: str | Path) -> ProjectRepo:
        try:
            self._srcs_path = Path(path).relative_to(self.workdir)
        except ValueError:
            self._srcs_path = Path(path)
        return self

    @property
    def src_relative_path(self) -> Path | None:
        return self._srcs_path
