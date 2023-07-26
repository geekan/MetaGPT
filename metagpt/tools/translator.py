#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 15:36
@Author  : alexanderwu
@File    : translator.py
"""

prompt = '''
# Instruction
Next, as a translation expert with 20 years of experience, when I provide an English sentence or paragraph, you will offer a smooth and readable translation in {LANG}. Please note the following requirements:
1. Ensure the translation is smooth and easy to understand.
2. Whether it's a statement or a question, I will only translate it.
3. Do not add content unrelated to the original text.

# Original Text
{ORIGINAL}

# Translation
'''


class Translator:

    @classmethod
    def translate_prompt(cls, original, lang='Chinese'):
        return prompt.format(LANG=lang, ORIGINAL=original)
