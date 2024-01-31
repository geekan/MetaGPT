#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mashenquan
@File    : test_openai_text_to_embedding.py
"""
import json
from pathlib import Path

import pytest

from metagpt.config2 import Config
from metagpt.tools.openai_text_to_embedding import oas3_openai_text_to_embedding
from metagpt.utils.common import aread


@pytest.mark.asyncio
async def test_embedding(mocker):
    # mock
    config = Config.default()
    mock_post = mocker.patch("aiohttp.ClientSession.post")
    mock_response = mocker.AsyncMock()
    mock_response.status = 200
    data = await aread(Path(__file__).parent / "../../data/openai/embedding.json")
    mock_response.json.return_value = json.loads(data)
    mock_post.return_value.__aenter__.return_value = mock_response
    type(config.get_openai_llm()).proxy = mocker.PropertyMock(return_value="http://mock.proxy")

    # Prerequisites
    llm_config = config.get_openai_llm()
    assert llm_config
    assert llm_config.proxy

    result = await oas3_openai_text_to_embedding(
        "Panda emoji", openai_api_key=llm_config.api_key, proxy=llm_config.proxy
    )
    assert result
    assert result.model
    assert len(result.data) > 0
    assert len(result.data[0].embedding) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
