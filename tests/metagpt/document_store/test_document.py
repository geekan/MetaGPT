#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/11 19:46
@Author  : alexanderwu
@File    : test_document.py
"""
import pytest

from metagpt.const import METAGPT_ROOT
from metagpt.document import IndexableDocument

CASES = [
    ("requirements.txt", None, None, 0),
    # ("cases/faq.csv", "Question", "Answer", 1),
    # ("cases/faq.json", "Question", "Answer", 1),
    # ("docx/faq.docx", None, None, 1),
    # ("cases/faq.pdf", None, None, 0),  # 这是因为pdf默认没有分割段落
    # ("cases/faq.txt", None, None, 0),  # 这是因为txt按照256分割段落
]


@pytest.mark.parametrize("relative_path, content_col, meta_col, threshold", CASES)
def test_document(relative_path, content_col, meta_col, threshold):
    doc = IndexableDocument.from_path(METAGPT_ROOT / relative_path, content_col, meta_col)
    rsp = doc.get_docs_and_metadatas()
    assert len(rsp[0]) > threshold
    assert len(rsp[1]) > threshold
