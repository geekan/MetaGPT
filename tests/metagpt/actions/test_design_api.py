#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:26
@Author  : alexanderwu
@File    : test_design_api.py
"""
import pytest

from metagpt.logs import logger

from metagpt.actions.design_api import WriteDesign
from metagpt.llm import LLM
from metagpt.roles.architect import Architect


@pytest.mark.asyncio
async def test_design_api():
    prd = "我们需要一个音乐播放器，它应该有播放、暂停、上一曲、下一曲等功能。"

    design_api = WriteDesign("design_api")

    result = await design_api.run(prd)
    logger.info(result)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_design_api_calculator():
    prd = """产品/功能介绍：基于大语言模型的、私有知识库的搜索引擎

目标：实现一个高效、准确、易用的搜索引擎，能够满足用户对私有知识库的搜索需求，提高工作效率和信息检索的准确性。

用户和使用场景：该搜索引擎主要面向需要频繁使用私有知识库进行信息检索的用户，例如企业内部的知识管理者、研发人员和数据分析师等。用户需要通过输入关键词或短语，快速地获取与其相关的知识库内容。

需求：
1. 支持基于大语言模型的搜索算法，能够对用户输入的关键词或短语进行语义理解，提高搜索结果的准确性。
2. 支持私有知识库的建立和维护，能够对知识库内容进行分类、标签和关键词的管理，方便用户进行信息检索。
3. 提供简洁、直观的用户界面，支持多种搜索方式（如全文搜索、精确搜索、模糊搜索等），方便用户进行快速检索。
4. 支持搜索结果的排序和过滤，能够根据相关度、时间等因素对搜索结果进行排序，方便用户找到最相关的信息。
5. 支持多种数据格式的导入和导出，方便用户对知识库内容进行备份和分享。

约束与限制：由于资源有限，需要在保证产品质量的前提下，控制开发成本和时间。同时，需要考虑用户的隐私保护和知识库内容的安全性。

性能指标：
1. 搜索响应时间：搜索引擎的搜索响应时间应该在毫秒级别，能够快速响应用户的搜索请求。
2. 搜索准确率：搜索引擎应该能够准确地返回与用户搜索意图相关的知识库内容，提高搜索结果的准确率。
3. 系统稳定性：搜索引擎应该具备良好的稳定性和可靠性，能够在高并发、大数据量等情况下保持正常运行。
4. 用户体验：搜索引擎的用户界面应该简洁、直观、易用，让用户能够快速地找到所需的信息。"""

    design_api = WriteDesign("design_api")
    result = await design_api.run(prd)
    logger.info(result)

    assert len(result) > 10
