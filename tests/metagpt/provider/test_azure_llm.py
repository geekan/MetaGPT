#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from metagpt.provider import AzureOpenAILLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_azure


def test_azure_llm():
    llm = AzureOpenAILLM(mock_llm_config_azure)
    kwargs = llm._make_client_kwargs()
    assert kwargs["azure_endpoint"] == mock_llm_config_azure.base_url
