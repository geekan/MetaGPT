#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/11 11:53
@Author  : femto Zheng
@File    : test_json_to_markdown.py
"""

from metagpt.utils.json_to_markdown import json_to_markdown


def test_json_to_markdown():
    # Example nested JSON data
    json_data = {
        "title": "Sample JSON to Markdown Conversion",
        "description": "Convert JSON to Markdown with headings and lists.",
        "tags": ["json", "markdown", "conversion"],
        "content": {
            "section1": {"subsection1": "This is a subsection.", "subsection2": "Another subsection."},
            "section2": "This is the second section content.",
        },
    }

    # Convert JSON to Markdown with nested sections
    markdown_output = json_to_markdown(json_data)

    expected = """## title

Sample JSON to Markdown Conversion

## description

Convert JSON to Markdown with headings and lists.

## tags

- json
- markdown
- conversion

## content

### section1

#### subsection1

This is a subsection.

#### subsection2

Another subsection.

### section2

This is the second section content.

"""
    # Print or use the generated Markdown
    # print(markdown_output)
    assert expected == markdown_output
