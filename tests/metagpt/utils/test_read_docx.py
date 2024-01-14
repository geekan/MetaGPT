#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 16:02
@Author  : alexanderwu
@File    : test_read_docx.py
"""
import pytest

from metagpt.const import METAGPT_ROOT
from metagpt.utils.read_document import read_docx


@pytest.mark.skip  # https://copyprogramming.com/howto/python-docx-error-opening-file-bad-magic-number-for-file-header-eoferror
class TestReadDocx:
    def test_read_docx(self):
        docx_sample = METAGPT_ROOT / "tests/data/docx_for_test.docx"
        docx = read_docx(docx_sample)
        assert len(docx) == 6
