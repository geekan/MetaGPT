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
from metagpt.const import REQUIREMENT_FILENAME
from metagpt.context import Context
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_prepare_documents():
    msg = Message(content="New user requirements balabala...")
    context = Context()

    await PrepareDocuments(context=context).run(with_messages=[msg])
    assert context.git_repo
    assert context.repo
    doc = await context.repo.docs.get(filename=REQUIREMENT_FILENAME)
    assert doc
    assert doc.content == msg.content
