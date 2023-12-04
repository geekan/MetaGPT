#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/6
@Author  : mashenquan
@File    : test_prepare_documents.py
@Desc: Unit test for prepare_documents.py
"""
import pytest

from metagpt.actions.prepare_documents import PrepareDocuments
from metagpt.config import CONFIG
from metagpt.const import DOCS_FILE_REPO, REQUIREMENT_FILENAME
from metagpt.schema import Message
from metagpt.utils.file_repository import FileRepository


@pytest.mark.asyncio
async def test_prepare_documents():
    msg = Message(content="New user requirements balabala...")

    if CONFIG.git_repo:
        CONFIG.git_repo.delete_repository()
        CONFIG.git_repo = None

    await PrepareDocuments().run(with_messages=[msg])
    assert CONFIG.git_repo
    doc = await FileRepository.get_file(filename=REQUIREMENT_FILENAME, relative_path=DOCS_FILE_REPO)
    assert doc
    assert doc.content == msg.content
