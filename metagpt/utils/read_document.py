#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 15:45
@Author  : alexanderwu
@File    : read_document.py
"""

import docx


def read_docx(file_path: str) -> list:
    """Open a docx file"""
    doc = docx.Document(file_path)

    # Create an empty list to store paragraph contents
    paragraphs_list = []

    # Iterate through the paragraphs in the document and add their content to the list
    for paragraph in doc.paragraphs:
        paragraphs_list.append(paragraph.text)

    return paragraphs_list
