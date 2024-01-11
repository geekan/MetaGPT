#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/8
@Author  : mashenquan
"""
import uuid
from pathlib import Path

import pytest

from metagpt.const import (
    BUGFIX_FILENAME,
    PACKAGE_REQUIREMENTS_FILENAME,
    PRDS_FILE_REPO,
    REQUIREMENT_FILENAME,
)
from metagpt.utils.project_repo import ProjectRepo


async def test_project_repo():
    root = Path(__file__).parent / f"../../../workspace/unittest/{uuid.uuid4().hex}"
    root = root.resolve()

    pr = ProjectRepo(root=str(root))
    assert pr.git_repo.workdir == root
    assert pr.workdir == pr.git_repo.workdir

    await pr.save(filename=REQUIREMENT_FILENAME, content=REQUIREMENT_FILENAME)
    doc = await pr.get(filename=REQUIREMENT_FILENAME)
    assert doc.content == REQUIREMENT_FILENAME
    await pr.save(filename=BUGFIX_FILENAME, content=BUGFIX_FILENAME)
    doc = await pr.get(filename=BUGFIX_FILENAME)
    assert doc.content == BUGFIX_FILENAME
    await pr.save(filename=PACKAGE_REQUIREMENTS_FILENAME, content=PACKAGE_REQUIREMENTS_FILENAME)
    doc = await pr.get(filename=PACKAGE_REQUIREMENTS_FILENAME)
    assert doc.content == PACKAGE_REQUIREMENTS_FILENAME
    await pr.docs.prd.save(filename="1.prd", content="1.prd", dependencies=[REQUIREMENT_FILENAME])
    doc = await pr.docs.prd.get(filename="1.prd")
    assert doc.content == "1.prd"
    await pr.resources.prd.save(
        filename="1.prd",
        content="1.prd",
        dependencies=[REQUIREMENT_FILENAME, f"{PRDS_FILE_REPO}/1.prd"],
    )
    doc = await pr.resources.prd.get(filename="1.prd")
    assert doc.content == "1.prd"
    dependencies = await pr.resources.prd.get_dependency(filename="1.prd")
    assert len(dependencies) == 2

    assert pr.changed_files
    assert pr.docs.prd.changed_files
    assert not pr.tests.changed_files

    with pytest.raises(ValueError):
        pr.srcs
    assert pr.with_src_path("test_src").srcs.root_path == Path("test_src")
    assert pr.src_relative_path == Path("test_src")

    pr.git_repo.delete_repository()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
