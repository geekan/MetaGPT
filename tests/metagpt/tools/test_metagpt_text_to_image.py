#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mashenquan
@File    : test_metagpt_text_to_image.py
"""
import base64
from unittest.mock import AsyncMock

import pytest

from metagpt.config2 import config
from metagpt.tools.metagpt_text_to_image import oas3_metagpt_text_to_image


@pytest.mark.asyncio
async def test_draw(mocker):
    # mock
    mock_post = mocker.patch("aiohttp.ClientSession.post")
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"images": [base64.b64encode(b"success")], "parameters": {"size": 1110}}
    mock_post.return_value.__aenter__.return_value = mock_response

    # Prerequisites
    assert config.metagpt_tti_url

    binary_data = await oas3_metagpt_text_to_image("Panda emoji")
    assert binary_data


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
