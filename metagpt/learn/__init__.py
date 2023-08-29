#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/30 20:57
@Author  : alexanderwu
@File    : __init__.py
"""

from metagpt.learn.text_to_image import text_to_image
from metagpt.learn.text_to_speech import text_to_speech

__all__ = [
    "text_to_image",
    "text_to_speech",
]