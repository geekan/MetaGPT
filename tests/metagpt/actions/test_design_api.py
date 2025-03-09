#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:26
@Author  : alexanderwu
@File    : test_design_api.py
@Modifiled By: mashenquan, 2023-12-6. According to RFC 135
"""
from pathlib import Path

import pytest

from metagpt.actions.design_api import WriteDesign
from metagpt.const import DEFAULT_WORKSPACE_ROOT, METAGPT_ROOT
from metagpt.logs import logger
from metagpt.schema import AIMessage, Message
from metagpt.utils.project_repo import ProjectRepo
from tests.data.incremental_dev_project.mock import DESIGN_SAMPLE, REFINED_PRD_JSON


@pytest.mark.asyncio
async def test_design(context):
    # Mock new design env
    prd = "我们需要一个音乐播放器，它应该有播放、暂停、上一曲、下一曲等功能。"
    context.kwargs.project_path = context.config.project_path
    context.kwargs.inc = False
    filename = "prd.txt"
    repo = ProjectRepo(context.kwargs.project_path)
    await repo.docs.prd.save(filename=filename, content=prd)
    kvs = {
        "project_path": str(context.kwargs.project_path),
        "changed_prd_filenames": [str(repo.docs.prd.workdir / filename)],
    }
    instruct_content = AIMessage.create_instruct_value(kvs=kvs, class_name="WritePRDOutput")

    design_api = WriteDesign(context=context)
    result = await design_api.run([Message(content=prd, instruct_content=instruct_content)])
    logger.info(result)
    assert result
    assert isinstance(result, AIMessage)
    assert result.instruct_content
    assert repo.docs.system_design.changed_files

    # Mock incremental design env
    context.kwargs.inc = True
    await repo.docs.prd.save(filename=filename, content=str(REFINED_PRD_JSON))
    await repo.docs.system_design.save(filename=filename, content=DESIGN_SAMPLE)

    result = await design_api.run([Message(content="", instruct_content=instruct_content)])
    logger.info(result)
    assert result
    assert isinstance(result, AIMessage)
    assert result.instruct_content
    assert repo.docs.system_design.changed_files


@pytest.mark.parametrize(
    ("user_requirement", "prd_filename", "legacy_design_filename"),
    [
        ("我们需要一个音乐播放器，它应该有播放、暂停、上一曲、下一曲等功能。", None, None),
        ("write 2048 game", str(METAGPT_ROOT / "tests/data/prd.json"), None),
        (
            "write 2048 game",
            str(METAGPT_ROOT / "tests/data/prd.json"),
            str(METAGPT_ROOT / "tests/data/system_design.json"),
        ),
    ],
)
@pytest.mark.asyncio
async def test_design_api(context, user_requirement, prd_filename, legacy_design_filename):
    action = WriteDesign()
    result = await action.run(
        user_requirement=user_requirement, prd_filename=prd_filename, legacy_design_filename=legacy_design_filename
    )
    assert isinstance(result, str)
    assert result
    assert str(DEFAULT_WORKSPACE_ROOT) in result


@pytest.mark.parametrize(
    ("user_requirement", "prd_filename", "legacy_design_filename"),
    [
        ("我们需要一个音乐播放器，它应该有播放、暂停、上一曲、下一曲等功能。", None, None),
        ("write 2048 game", str(METAGPT_ROOT / "tests/data/prd.json"), None),
        (
            "write 2048 game",
            str(METAGPT_ROOT / "tests/data/prd.json"),
            str(METAGPT_ROOT / "tests/data/system_design.json"),
        ),
    ],
)
@pytest.mark.asyncio
async def test_design_api_dir(context, user_requirement, prd_filename, legacy_design_filename):
    action = WriteDesign()
    result = await action.run(
        user_requirement=user_requirement,
        prd_filename=prd_filename,
        legacy_design_filename=legacy_design_filename,
        output_pathname=str(Path(context.config.project_path) / "1.txt"),
    )
    assert isinstance(result, str)
    assert result
    assert str(context.config.project_path) in result


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
