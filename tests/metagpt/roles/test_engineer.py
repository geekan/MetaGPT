#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 10:14
@Author  : alexanderwu
@File    : test_engineer.py
@Modified By: mashenquan, 2023-11-1. In accordance with Chapter 2.2.1 and 2.2.2 of RFC 116, utilize the new message
        distribution feature for message handling.
"""
import json
from pathlib import Path

import pytest

from metagpt.actions import WriteCode, WriteTasks
from metagpt.config import CONFIG
from metagpt.const import (
    PRDS_FILE_REPO,
    REQUIREMENT_FILENAME,
    SYSTEM_DESIGN_FILE_REPO,
    TASK_FILE_REPO,
)
from metagpt.logs import logger
from metagpt.roles.engineer import Engineer
from metagpt.schema import CodingContext, Message
from metagpt.utils.common import CodeParser, any_to_name, any_to_str, aread, awrite
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.git_repository import ChangeType
from tests.metagpt.roles.mock import STRS_FOR_PARSING, TASKS, MockMessages


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_engineer():
    # Prerequisites
    rqno = "20231221155954.json"
    await FileRepository.save_file(REQUIREMENT_FILENAME, content=MockMessages.req.content)
    await FileRepository.save_file(rqno, relative_path=PRDS_FILE_REPO, content=MockMessages.prd.content)
    await FileRepository.save_file(
        rqno, relative_path=SYSTEM_DESIGN_FILE_REPO, content=MockMessages.system_design.content
    )
    await FileRepository.save_file(rqno, relative_path=TASK_FILE_REPO, content=MockMessages.json_tasks.content)

    engineer = Engineer()
    rsp = await engineer.run(Message(content="", cause_by=WriteTasks))

    logger.info(rsp)
    assert rsp.cause_by == any_to_str(WriteCode)
    src_file_repo = CONFIG.git_repo.new_file_repository(CONFIG.src_workspace)
    assert src_file_repo.changed_files


def test_parse_str():
    for idx, i in enumerate(STRS_FOR_PARSING):
        text = CodeParser.parse_str(f"{idx + 1}", i)
        # logger.info(text)
        assert text == "a"


def test_parse_blocks():
    tasks = CodeParser.parse_blocks(TASKS)
    logger.info(tasks.keys())
    assert "Task list" in tasks.keys()


target_list = [
    "smart_search_engine/knowledge_base.py",
    "smart_search_engine/index.py",
    "smart_search_engine/ranking.py",
    "smart_search_engine/summary.py",
    "smart_search_engine/search.py",
    "smart_search_engine/main.py",
    "smart_search_engine/interface.py",
    "smart_search_engine/user_feedback.py",
    "smart_search_engine/security.py",
    "smart_search_engine/testing.py",
    "smart_search_engine/monitoring.py",
]


def test_parse_file_list():
    tasks = CodeParser.parse_file_list("Task list", TASKS)
    logger.info(tasks)
    assert isinstance(tasks, list)
    assert target_list == tasks


target_code = """task_list = [
    "smart_search_engine/knowledge_base.py",
    "smart_search_engine/index.py",
    "smart_search_engine/ranking.py",
    "smart_search_engine/summary.py",
    "smart_search_engine/search.py",
    "smart_search_engine/main.py",
    "smart_search_engine/interface.py",
    "smart_search_engine/user_feedback.py",
    "smart_search_engine/security.py",
    "smart_search_engine/testing.py",
    "smart_search_engine/monitoring.py",
]
"""


def test_parse_code():
    code = CodeParser.parse_code("Task list", TASKS, lang="python")
    logger.info(code)
    assert isinstance(code, str)
    assert target_code == code


def test_todo():
    role = Engineer()
    assert role.todo == any_to_name(WriteCode)


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_new_coding_context():
    # Prerequisites
    demo_path = Path(__file__).parent / "../../data/demo_project"
    deps = json.loads(await aread(demo_path / "dependencies.json"))
    dependency = await CONFIG.git_repo.get_dependency()
    for k, v in deps.items():
        await dependency.update(k, set(v))
    data = await aread(demo_path / "system_design.json")
    rqno = "20231221155954.json"
    await awrite(CONFIG.git_repo.workdir / SYSTEM_DESIGN_FILE_REPO / rqno, data)
    data = await aread(demo_path / "tasks.json")
    await awrite(CONFIG.git_repo.workdir / TASK_FILE_REPO / rqno, data)

    CONFIG.src_workspace = Path(CONFIG.git_repo.workdir) / "game_2048"
    src_file_repo = CONFIG.git_repo.new_file_repository(relative_path=CONFIG.src_workspace)
    task_file_repo = CONFIG.git_repo.new_file_repository(relative_path=TASK_FILE_REPO)
    design_file_repo = CONFIG.git_repo.new_file_repository(relative_path=SYSTEM_DESIGN_FILE_REPO)

    filename = "game.py"
    ctx_doc = await Engineer._new_coding_doc(
        filename=filename,
        src_file_repo=src_file_repo,
        task_file_repo=task_file_repo,
        design_file_repo=design_file_repo,
        dependency=dependency,
    )
    assert ctx_doc
    assert ctx_doc.filename == filename
    assert ctx_doc.content
    ctx = CodingContext.model_validate_json(ctx_doc.content)
    assert ctx.filename == filename
    assert ctx.design_doc
    assert ctx.design_doc.content
    assert ctx.task_doc
    assert ctx.task_doc.content
    assert ctx.code_doc

    CONFIG.git_repo.add_change({f"{TASK_FILE_REPO}/{rqno}": ChangeType.UNTRACTED})
    CONFIG.git_repo.commit("mock env")
    await src_file_repo.save(filename=filename, content="content")
    role = Engineer()
    assert not role.code_todos
    await role._new_code_actions()
    assert role.code_todos


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
