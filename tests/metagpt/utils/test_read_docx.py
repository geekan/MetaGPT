#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 16:02
@Author  : alexanderwu
@File    : test_read_docx.py
"""

from metagpt.const import PROJECT_ROOT
from metagpt.utils.read_document import read_docx


class TestReadDocx:
    def test_read_docx(self):
        docx_sample = PROJECT_ROOT / "tests/data/docx_for_test.docx"
        docx = read_docx(docx_sample)
        assert len(docx) == 6
