#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 12:01
@Author  : alexanderwu
@File    : test_qa_engineer.py
"""
from pathlib import Path
from typing import List
import json

import pytest
from pydantic import BaseModel, Field
from unittest.mock import AsyncMock, MagicMock

from metagpt.actions import DebugError, RunCode, WriteTest, UserRequirement
from metagpt.actions.summarize_code import SummarizeCode
from metagpt.actions.prepare_documents import PrepareDocuments
from metagpt.environment import Environment
from metagpt.roles import QaEngineer
from metagpt.schema import Message, AIMessage, Document, RunCodeContext, TestingContext
from metagpt.utils.common import any_to_str, aread, awrite
from metagpt.utils.project_repo import ProjectRepo


class MockProjectRepo:
    def __init__(self, workdir):
        self.workdir = Path(workdir)
        self.srcs = MockRepoFiles(self.workdir / "src")
        self.tests = MockRepoFiles(self.workdir / "tests")
        self.test_outputs = MockRepoFiles(self.workdir / "test_outputs")
        self.src_relative_path = None

    def with_src_path(self, path):
        self.src_relative_path = path
        return self


class MockRepoFiles:
    def __init__(self, workdir):
        self.workdir = Path(workdir)
        self.root_path = workdir
        self.changed_files = {}

    async def get(self, filename):
        if filename.endswith(".py"):
            return Document(root_path=str(self.root_path), filename=filename, content="def test(): pass")
        return None

    async def save(self, filename, content, dependencies=None):
        self.changed_files[filename] = content
        return Document(root_path=str(self.root_path), filename=filename, content=content)

    async def save_doc(self, doc, dependencies=None):
        self.changed_files[doc.filename] = doc.content
        return doc


class MockContext(BaseModel):
    reqa_file: str = None
    src_workspace: Path = None
    git_repo: BaseModel = None

    class Config:
        arbitrary_types_allowed = True


class MockGitRepo:
    def __init__(self, workdir):
        self.workdir = workdir
        self.name = "test_project"


class MockEnv(Environment):
    msgs: List[Message] = Field(default_factory=list)

    def publish_message(self, message: Message, peekable: bool = True) -> bool:
        self.msgs.append(message)
        return True


@pytest.fixture
def mock_env():
    return MockEnv()


@pytest.fixture
def mock_repo(tmp_path):
    return MockProjectRepo(tmp_path)


@pytest.fixture
def qa_engineer(mock_env, mock_repo):
    role = QaEngineer()
    role.set_env(mock_env)
    role.repo = mock_repo
    return role


@pytest.mark.asyncio
async def test_initialization():
    """Test QaEngineer initialization"""
    role = QaEngineer()
    assert role.name == "Edward"
    assert role.profile == "QaEngineer"
    assert role.test_round == 0
    assert role.test_round_allowed == 5
    assert not role.enable_memory


@pytest.mark.asyncio
async def test_write_test(qa_engineer, mock_repo):
    """Test _write_test method"""
    context = MockContext(reqa_file="test.py")
    qa_engineer.context = context
    message = Message(content="Test content")

    await qa_engineer._write_test(message)

    assert "test_test.py" in mock_repo.tests.changed_files
    assert mock_repo.tests.changed_files["test_test.py"] is not None


@pytest.mark.asyncio
async def test_run_code(qa_engineer, mock_repo):
    """Test _run_code method"""
    context = RunCodeContext(
        command=["python", "test_sample.py"],
        code_filename="sample.py",
        test_filename="test_sample.py",
        working_directory=str(mock_repo.workdir),
    )
    message = Message(content=context.model_dump_json())

    await qa_engineer._run_code(message)

    assert "test_sample.py.json" in mock_repo.test_outputs.changed_files


@pytest.mark.asyncio
async def test_parse_user_requirement(qa_engineer):
    """Test _parse_user_requirement method"""
    qa_engineer.git_repo = MockGitRepo(Path("/test/path"))
    message = Message(
        content="Create test for game.py",
        cause_by=any_to_str(UserRequirement)
    )

    result = await qa_engineer._parse_user_requirement(message)
    assert isinstance(result, AIMessage)


@pytest.mark.asyncio
async def test_think_with_summarize_code(qa_engineer):
    """Test _think method with SummarizeCode message"""

    class MockArgs(BaseModel):
        project_path: str = "/test/path"

    message = Message(
        content="Test content",
        cause_by=any_to_str(SummarizeCode),
        instruct_content=MockArgs()
    )
    qa_engineer.rc.news = [message]

    result = await qa_engineer._think()
    assert result is True
    assert qa_engineer.input_args is not None
    assert qa_engineer.repo is not None


@pytest.mark.asyncio
async def test_act_exceeding_rounds(qa_engineer):
    """Test _act method when exceeding test rounds"""
    qa_engineer.test_round = 6
    qa_engineer.input_args = BaseModel()

    result = await qa_engineer._act()
    assert isinstance(result, AIMessage)
    assert "Exceeding" in result.content


@pytest.mark.asyncio
async def test_qa_full_workflow(tmp_path):
    """Test the full QA workflow"""
    # Setup mock context and environment
    git_repo = MockGitRepo(tmp_path)
    context = MockContext(src_workspace=tmp_path / "qa/game_2048", git_repo=git_repo)
    context.src_workspace.parent.mkdir(parents=True, exist_ok=True)

    # Create mock game.py file
    await awrite(filename=context.src_workspace / "game.py", data="def test(): pass", encoding="utf-8")
    await awrite(filename=tmp_path / "requirements.txt", data="")

    # Setup QA engineer
    env = MockEnv()
    role = QaEngineer(context=context)
    role.set_env(env)
    role.repo = MockProjectRepo(tmp_path)

    # Test full workflow
    await role.run(with_message=Message(content="", cause_by=SummarizeCode))
    assert env.msgs
    assert env.msgs[0].cause_by == any_to_str(WriteTest)

    msg = env.msgs[0]
    env.msgs.clear()
    await role.run(with_message=msg)
    assert env.msgs
    assert env.msgs[0].cause_by == any_to_str(RunCode)

    msg = env.msgs[0]
    env.msgs.clear()
    await role.run(with_message=msg)
    assert env.msgs
    assert env.msgs[0].cause_by == any_to_str(DebugError)

    msg = env.msgs[0]
    env.msgs.clear()
    role.test_round_allowed = 1
    rsp = await role.run(with_message=msg)
    assert "Exceeding" in rsp.content