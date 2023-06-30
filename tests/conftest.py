#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/1 12:10
@Author  : alexanderwu
@File    : conftest.py
"""

from unittest.mock import Mock
import pytest
from metagpt.logs import logger

from metagpt.provider.openai_api import OpenAIGPTAPI as GPTAPI


class Context:
    def __init__(self):
        self._llm_ui = None
        self._llm_api = GPTAPI()

    @property
    def llm_api(self):
        return self._llm_api


@pytest.fixture(scope="package")
def llm_api():
    logger.info("Setting up the test")
    _context = Context()

    yield _context.llm_api

    logger.info("Tearing down the test")


@pytest.fixture(scope="function")
def mock_llm():
    # Create a mock LLM for testing
    return Mock()