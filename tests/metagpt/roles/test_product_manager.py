#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/16 14:50
@Author  : alexanderwu
@File    : test_product_manager.py
"""
import json

import pytest

from metagpt.actions import WritePRD
from metagpt.actions.prepare_documents import PrepareDocuments
from metagpt.const import REQUIREMENT_FILENAME
from metagpt.context import Context
from metagpt.logs import logger
from metagpt.roles import ProductManager
from metagpt.utils.common import any_to_str
from tests.metagpt.roles.mock import MockMessages


@pytest.mark.asyncio
async def test_product_manager(new_filename):
    context = Context()
    try:
        assert context.git_repo is None
        assert context.repo is None
        product_manager = ProductManager(context=context)
        # prepare documents
        rsp = await product_manager.run(MockMessages.req)
        assert context.git_repo
        assert context.repo
        assert rsp.cause_by == any_to_str(PrepareDocuments)
        assert REQUIREMENT_FILENAME in context.repo.docs.changed_files

        # write prd
        rsp = await product_manager.run(rsp)
        assert rsp.cause_by == any_to_str(WritePRD)
        logger.info(rsp)
        assert len(rsp.content) > 0
        doc = list(rsp.instruct_content.docs.values())[0]
        m = json.loads(doc.content)
        assert m["Original Requirements"] == MockMessages.req.content

        # nothing to do
        rsp = await product_manager.run(rsp)
        assert rsp is None
    except Exception as e:
        assert not e
    finally:
        context.git_repo.delete_repository()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
