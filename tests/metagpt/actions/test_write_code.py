#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_code.py
@Modifiled By: mashenquan, 2023-12-6. According to RFC 135
"""
import json
from pathlib import Path

import pytest

from metagpt.actions.write_code import WriteCode
from metagpt.logs import logger
from metagpt.schema import CodingContext, Document
from metagpt.utils.common import CodeParser, aread
from metagpt.utils.project_repo import ProjectRepo
from tests.data.incremental_dev_project.mock import (
    CODE_PLAN_AND_CHANGE_SAMPLE,
    REFINED_CODE_INPUT_SAMPLE,
    REFINED_DESIGN_JSON,
    REFINED_TASK_JSON,
)
from tests.metagpt.actions.mock_markdown import TASKS_2, WRITE_CODE_PROMPT_SAMPLE


def setup_inc_workdir(context, inc: bool = False):
    """setup incremental workdir for testing"""
    if inc:
        context.config.inc = inc
        context.config.project_path = "old"

    return context


@pytest.mark.asyncio
async def test_write_code(context):
    # Prerequisites
    repo = ProjectRepo(context.config.project_path)
    repo.with_src_path("writecode")

    coding_ctx = CodingContext(
        filename="task_filename.py", design_doc=Document(content="设计一个名为'add'的函数，该函数接受两个整数作为输入，并返回它们的和。")
    )
    doc = Document(content=coding_ctx.model_dump_json())
    write_code = WriteCode(i_context=doc, context=context)

    code = await write_code.run()
    logger.info(code.model_dump_json())

    # 我们不能精确地预测生成的代码，但我们可以检查某些关键字
    assert "def add" in code.code_doc.content
    assert "return" in code.code_doc.content


@pytest.mark.asyncio
async def test_write_code_directly(context):
    prompt = WRITE_CODE_PROMPT_SAMPLE + "\n" + TASKS_2[0]
    llm = context.llm_with_cost_manager_from_llm_config(context.config.llm)
    rsp = await llm.aask(prompt)
    logger.info(rsp)


@pytest.mark.asyncio
async def test_write_code_deps(context):
    # Prerequisites
    repo = ProjectRepo(context.config.project_path)
    repo.with_src_path("snake1/snake1")
    demo_path = Path(__file__).parent / "../../data/demo_project"
    await repo.test_outputs.save(
        filename="test_game.py.json", content=await aread(str(demo_path / "test_game.py.json"))
    )
    await repo.docs.code_summary.save(
        filename="20231221155954.json",
        content=await aread(str(demo_path / "code_summaries.json")),
    )
    await repo.docs.system_design.save(
        filename="20231221155954.json",
        content=await aread(str(demo_path / "system_design.json")),
    )
    await repo.docs.task.save(filename="20231221155954.json", content=await aread(str(demo_path / "tasks.json")))
    await repo.srcs.save(filename="main.py", content='if __name__ == "__main__":\nmain()')
    ccontext = CodingContext(
        filename="game.py",
        design_doc=await repo.docs.system_design.get(filename="20231221155954.json"),
        task_doc=await repo.docs.task.get(filename="20231221155954.json"),
        code_doc=Document(filename="game.py", content="", root_path="snake1"),
    )
    coding_doc = Document(root_path="snake1", filename="game.py", content=ccontext.model_dump_json())

    action = WriteCode(i_context=coding_doc, context=context)
    rsp = await action.run()
    assert rsp
    assert rsp.code_doc.content


@pytest.mark.asyncio
async def test_write_refined_code(context, git_dir):
    # Prerequisites
    context = setup_inc_workdir(context, inc=True)
    repo = ProjectRepo(context.config.project_path)
    await repo.docs.system_design.save(filename="1.json", content=json.dumps(REFINED_DESIGN_JSON))
    await repo.docs.task.save(filename="1.json", content=json.dumps(REFINED_TASK_JSON))
    await repo.docs.code_plan_and_change.save(filename="1.json", content=json.dumps(CODE_PLAN_AND_CHANGE_SAMPLE))

    # old_workspace contains the legacy code
    await repo.srcs.save(filename="game.py", content=CodeParser.parse_code(block="", text=REFINED_CODE_INPUT_SAMPLE))

    ccontext = CodingContext(
        filename="game.py",
        design_doc=await repo.docs.system_design.get(filename="1.json"),
        task_doc=await repo.docs.task.get(filename="1.json"),
        code_plan_and_change_doc=await repo.docs.code_plan_and_change.get(filename="1.json"),
        code_doc=Document(filename="game.py", content="", root_path="src"),
    )
    coding_doc = Document(root_path="src", filename="game.py", content=ccontext.json())

    action = WriteCode(i_context=coding_doc, context=context)
    rsp = await action.run()
    assert rsp
    assert rsp.code_doc.content


@pytest.mark.asyncio
async def test_get_codes(context):
    # Prerequisites
    context = setup_inc_workdir(context, inc=True)
    repo = ProjectRepo(context.config.project_path)
    for filename in ["game.py", "ui.py"]:
        await repo.with_src_path(context.src_workspace).srcs.save(
            filename=filename, content=f"# {filename}\nnew code ..."
        )
        await repo.with_src_path(context.repo.old_workspace).srcs.save(
            filename=filename, content=f"# {filename}\nlegacy code ..."
        )

    await repo.with_src_path(context.repo.old_workspace).srcs.save(
        filename="gui.py", content="# gui.py\nlegacy code ..."
    )
    await repo.srcs.save(filename="main.py", content='# main.py\nif __name__ == "__main__":\n    main()')
    task_doc = Document(filename="1.json", content=json.dumps(REFINED_TASK_JSON))

    # Ready to write gui.py
    codes = await WriteCode.get_codes(task_doc=task_doc, exclude="gui.py", project_repo=repo)
    codes_inc = await WriteCode.get_codes(task_doc=task_doc, exclude="gui.py", project_repo=repo, use_inc=True)

    logger.info(codes)
    logger.info(codes_inc)
    assert codes
    assert codes_inc


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
