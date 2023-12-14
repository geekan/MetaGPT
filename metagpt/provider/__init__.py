#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 22:59
@Author  : alexanderwu
@File    : __init__.py
@Modified By: mashenquan, 2023-12-15. Add LLMType
"""
from enum import Enum


class LLMType(Enum):
    OPENAI = "OpenAI"
    METAGPT = "MetaGPT"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def get(cls, value):
        for member in cls:
            if member.value == value:
                return member
        return cls.UNKNOWN

    @classmethod
    def __missing__(cls, value):
        return cls.UNKNOWN
