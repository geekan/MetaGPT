#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : test_text_to_embedding.py
@Desc    : Unit tests.
"""
import json
from pathlib import Path

import pytest

from metagpt.config2 import Config
from metagpt.learn.text_to_embedding import text_to_embedding
from metagpt.utils.common import aread


@pytest.mark.asyncio
async def test_text_to_embedding(mocker):
    # mock
    config = Config.default()
    mock_post = mocker.patch("aiohttp.ClientSession.post")
    mock_response = mocker.AsyncMock()
    mock_response.status = 200
    data = await aread(Path(__file__).parent / "../../data/openai/embedding.json")
    mock_response.json.return_value = json.loads(data)
    mock_post.return_value.__aenter__.return_value = mock_response
    config.get_openai_llm().proxy = mocker.PropertyMock(return_value="http://mock.proxy")

    # Prerequisites
    assert config.get_openai_llm().api_key
    assert config.get_openai_llm().proxy

    v = await text_to_embedding(text="Panda emoji", config=config)
    assert len(v.data) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
