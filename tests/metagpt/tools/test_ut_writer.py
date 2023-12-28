#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/30 21:44
@Author  : alexanderwu
@File    : test_ut_writer.py
"""
from pathlib import Path

import pytest

from metagpt.config import CONFIG
from metagpt.const import API_QUESTIONS_PATH, UT_PY_PATH
from metagpt.tools.ut_writer import YFT_PROMPT_PREFIX, UTGenerator


class TestUTWriter:
    @pytest.mark.asyncio
    async def test_api_to_ut_sample(self):
        # Prerequisites
        swagger_file = Path(__file__).parent / "../../data/ut_writer/yft_swaggerApi.json"
        assert swagger_file.exists()
        assert CONFIG.OPENAI_API_KEY and CONFIG.OPENAI_API_KEY != "YOUR_API_KEY"
        assert not CONFIG.OPENAI_API_TYPE
        assert CONFIG.OPENAI_API_MODEL

        tags = ["测试", "作业"]
        # 这里在文件中手动加入了两个测试标签的API

        utg = UTGenerator(
            swagger_file=str(swagger_file),
            ut_py_path=UT_PY_PATH,
            questions_path=API_QUESTIONS_PATH,
            template_prefix=YFT_PROMPT_PREFIX,
        )
        ret = await utg.generate_ut(include_tags=tags)
        # 后续加入对文件生成内容与数量的检验
        assert ret


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
