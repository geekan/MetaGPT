#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 22:59
@Author  : alexanderwu
@File    : __init__.py
@Modified By: mashenquan, 2023/9/8. Add `MetaGPTLLMAPI`
"""

from metagpt.provider.openai_api import OpenAIGPTAPI
from metagpt.provider.metagpt_llm_api import MetaGPTLLMAPI


__all__ = ["OpenAIGPTAPI", "MetaGPTLLMAPI"]
