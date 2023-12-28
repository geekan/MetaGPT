#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : 

import pytest

from metagpt.provider.azure_openai_api import AzureOpenAILLM
from metagpt.config import CONFIG

CONFIG.OPENAI_API_VERSION = "xx"
CONFIG.openai_proxy = "http://127.0.0.1:80"  # fake value


def test_azure_openai_api():
    _ = AzureOpenAILLM()
