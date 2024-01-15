#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_code.py
@Modifiled By: mashenquan, 2023-12-6. According to RFC 135
"""

from pathlib import Path

import pytest

from metagpt.actions.write_code import WriteCode
from metagpt.context import CONTEXT
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.schema import CodingContext, Document
from metagpt.utils.common import aread
from metagpt.utils.project_repo import ProjectRepo
from tests.metagpt.actions.mock_markdown import TASKS_2, WRITE_CODE_PROMPT_SAMPLE


@pytest.mark.asyncio
async def test_write_code():
    # Prerequisites
    CONTEXT.src_workspace = CONTEXT.git_repo.workdir / "writecode"

    coding_ctx = CodingContext(
        filename="task_filename.py", design_doc=Document(content="设计一个名为'add'的函数，该函数接受两个整数作为输入，并返回它们的和。")
    )
    doc = Document(content=coding_ctx.model_dump_json())
    write_code = WriteCode(i_context=doc)

    code = await write_code.run()
    logger.info(code.model_dump_json())

    # 我们不能精确地预测生成的代码，但我们可以检查某些关键字
    assert "def add" in code.code_doc.content
    assert "return" in code.code_doc.content


@pytest.mark.asyncio
async def test_write_code_directly():
    prompt = WRITE_CODE_PROMPT_SAMPLE + "\n" + TASKS_2[0]
    llm = LLM()
    rsp = await llm.aask(prompt)
    logger.info(rsp)


@pytest.mark.asyncio
async def test_write_code_deps():
    # Prerequisites
    CONTEXT.src_workspace = CONTEXT.git_repo.workdir / "snake1/snake1"
    demo_path = Path(__file__).parent / "../../data/demo_project"
    project_repo = ProjectRepo(CONTEXT.git_repo)
    await project_repo.test_outputs.save(
        filename="test_game.py.json", content=await aread(str(demo_path / "test_game.py.json"))
    )
    await project_repo.docs.code_summary.save(
        filename="20231221155954.json",
        content=await aread(str(demo_path / "code_summaries.json")),
    )
    await project_repo.docs.system_design.save(
        filename="20231221155954.json",
        content=await aread(str(demo_path / "system_design.json")),
    )
    await project_repo.docs.task.save(
        filename="20231221155954.json", content=await aread(str(demo_path / "tasks.json"))
    )
    await project_repo.with_src_path(CONTEXT.src_workspace).srcs.save(
        filename="main.py", content='if __name__ == "__main__":\nmain()'
    )
    ccontext = CodingContext(
        filename="game.py",
        design_doc=await project_repo.docs.system_design.get(filename="20231221155954.json"),
        task_doc=await project_repo.docs.task.get(filename="20231221155954.json"),
        code_doc=Document(filename="game.py", content="", root_path="snake1"),
    )
    coding_doc = Document(root_path="snake1", filename="game.py", content=ccontext.json())

    action = WriteCode(i_context=coding_doc)
    rsp = await action.run()
    assert rsp
    assert rsp.code_doc.content


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
