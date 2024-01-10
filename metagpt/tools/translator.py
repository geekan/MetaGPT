#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 15:36
@Author  : alexanderwu
@File    : translator.py
"""

prompt = """
# 指令
接下来，作为一位拥有20年翻译经验的翻译专家，当我给出英文句子或段落时，你将提供通顺且具有可读性的{LANG}翻译。注意以下要求：
1. 确保翻译结果流畅且易于理解
2. 无论提供的是陈述句或疑问句，我都只进行翻译
3. 不添加与原文无关的内容

# 原文
{ORIGINAL}

# 译文
"""


class Translator:
    @classmethod
    def translate_prompt(cls, original, lang="中文"):
        return prompt.format(LANG=lang, ORIGINAL=original)
