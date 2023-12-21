#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/9/4 15:40:40
@Author  : Stitch-z
@File    : tutorial_assistant.py
@Describe : Tutorial Assistant's prompt templates.
"""

COMMON_PROMPT = """
You are now a seasoned technical professional in the field of the internet. 
We need you to write a technical tutorial with the topic "{topic}".
"""

DIRECTORY_PROMPT = (
    COMMON_PROMPT
    + """
Please provide the specific table of contents for this tutorial, strictly following the following requirements:
1. The output must be strictly in the specified language, {language}.
2. Answer strictly in the dictionary format like {{"title": "xxx", "directory": [{{"dir 1": ["sub dir 1", "sub dir 2"]}}, {{"dir 2": ["sub dir 3", "sub dir 4"]}}]}}.
3. The directory should be as specific and sufficient as possible, with a primary and secondary directory.The secondary directory is in the array.
4. Do not have extra spaces or line breaks.
5. Each directory title has practical significance.
"""
)

CONTENT_PROMPT = (
    COMMON_PROMPT
    + """
Now I will give you the module directory titles for the topic. 
Please output the detailed principle content of this title in detail. 
If there are code examples, please provide them according to standard code specifications. 
Without a code example, it is not necessary.

The module directory titles for the topic is as follows:
{directory}

Strictly limit output according to the following requirements:
1. Follow the Markdown syntax format for layout.
2. If there are code examples, they must follow standard syntax specifications, have document annotations, and be displayed in code blocks.
3. The output must be strictly in the specified language, {language}.
4. Do not have redundant output, including concluding remarks.
5. Strict requirement not to output the topic "{topic}".
"""
)
