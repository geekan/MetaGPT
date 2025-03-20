#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/11 11:50
@Author  : femto Zheng
@File    : json_to_markdown.py
"""


# since we original write docs/*.md in markdown format, so I convert json back to markdown
def json_to_markdown(data, depth=2):
    """
    Convert a JSON object to Markdown with headings for keys and lists for arrays, supporting nested objects.

    Args:
        data: JSON object (dictionary) or value.
        depth (int): Current depth level for Markdown headings.

    Returns:
        str: Markdown representation of the JSON data.
    """
    markdown = ""

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                # Handle JSON arrays
                markdown += "#" * depth + f" {key}\n\n"
                items = [str(item) for item in value]
                markdown += "- " + "\n- ".join(items) + "\n\n"
            elif isinstance(value, dict):
                # Handle nested JSON objects
                markdown += "#" * depth + f" {key}\n\n"
                markdown += json_to_markdown(value, depth + 1)
            else:
                # Handle other values
                markdown += "#" * depth + f" {key}\n\n{value}\n\n"
    else:
        # Handle non-dictionary JSON data
        markdown = str(data)

    return markdown
