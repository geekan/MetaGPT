#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/30 21:44
@Author  : alexanderwu
@File    : test_ut_generator.py
"""

from metagpt.const import API_QUESTIONS_PATH, SWAGGER_PATH, UT_PY_PATH
from metagpt.tools.ut_writer import YFT_PROMPT_PREFIX, UTGenerator


class TestUTWriter:
    def test_api_to_ut_sample(self):
        swagger_file = SWAGGER_PATH / "yft_swaggerApi.json"
        tags = ["测试"]  # "智能合同导入", "律师审查", "ai合同审查", "草拟合同&律师在线审查", "合同审批", "履约管理", "签约公司"]
        # 这里在文件中手动加入了两个测试标签的API

        utg = UTGenerator(swagger_file=swagger_file, ut_py_path=UT_PY_PATH, questions_path=API_QUESTIONS_PATH,
                          template_prefix=YFT_PROMPT_PREFIX)
        ret = utg.generate_ut(include_tags=tags)
        # 后续加入对文件生成内容与数量的检验
        assert ret
