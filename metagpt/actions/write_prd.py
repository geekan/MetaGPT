#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_prd.py
"""
from typing import List

from metagpt.actions import Action, ActionOutput
from metagpt.actions.search_and_summarize import SearchAndSummarize
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.utils.get_template import get_template

templates = {
    "json": {
        "PROMPT_TEMPLATE": """
# Context
{{
    "Original Requirements": "{requirements}",
    "Search Information": ""
}} 

## Format example
{format_example}
-----
Role: You are a professional product manager; the goal is to design a concise, usable, efficient product
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
Requirements: According to the context, fill in the following missing information, note that each sections are returned in Python code triple quote form seperatedly.
ATTENTION: Output carefully referenced "Format example" in format.

## YOU NEED TO FULFILL THE BELOW JSON DOC

{{
    "Language": "", # str, use the same language as the user requirement. en_us / zh_cn etc.
    "Original Requirements": "", # str, place the polished complete original requirements here
    "project_name": "", # str, name it like game_2048 / web_2048 / simple_crm etc.
    "Search Information": "",
    "Requirements": "", 
    "Product Goals": [], # Provided as Python list[str], up to 3 clear, orthogonal product goals.
    "User Stories": [], # Provided as Python list[str], up to 5 scenario-based user stories
    "Competitive Analysis": [], # Provided as Python list[str], up to 8 competitive product analyses
    # Use mermaid quadrantChart code syntax. up to 14 competitive products. Translation: Distribute these competitor scores evenly between 0 and 1, trying to conform to a normal distribution centered around 0.5 as much as possible.
    "Competitive Quadrant Chart": "quadrantChart
                title Reach and engagement of campaigns
                x-axis Low Reach --> High Reach
                y-axis Low Engagement --> High Engagement
                quadrant-1 We should expand
                quadrant-2 Need to promote
                quadrant-3 Re-evaluate
                quadrant-4 May be improved
                Campaign A: [0.3, 0.6]
                Campaign B: [0.45, 0.23]
                Campaign C: [0.57, 0.69]
                Campaign D: [0.78, 0.34]
                Campaign E: [0.40, 0.34]
                Campaign F: [0.35, 0.78]",
    "Requirement Analysis": "", # Provide as Plain text.
    "Requirement Pool": [["P0","P0 requirement"],["P1","P1 requirement"]], # Provided as Python list[list[str], the parameters are requirement description, priority(P0/P1/P2), respectively, comply with PEP standards
    "UI Design draft": "", # Provide as Plain text. Be simple. Describe the elements and functions, also provide a simple style description and layout description.
    "Anything UNCLEAR": "", # Provide as Plain text. Try to clarify it.
}}

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": """
[CONTENT]
{
    "Language": "",
    "Original Requirements": "",
    "Search Information": "",
    "Requirements": "",
    "Product Goals": [],
    "User Stories": [],
    "Competitive Analysis": [],
    "Competitive Quadrant Chart": "quadrantChart
                title Reach and engagement of campaigns
                x-axis Low Reach --> High Reach
                y-axis Low Engagement --> High Engagement
                quadrant-1 We should expand
                quadrant-2 Need to promote
                quadrant-3 Re-evaluate
                quadrant-4 May be improved
                Campaign A: [0.3, 0.6]
                Campaign B: [0.45, 0.23]
                Campaign C: [0.57, 0.69]
                Campaign D: [0.78, 0.34]
                Campaign E: [0.40, 0.34]
                Campaign F: [0.35, 0.78]",
    "Requirement Analysis": "",
    "Requirement Pool": [["P0","P0 requirement"],["P1","P1 requirement"]],
    "UI Design draft": "",
    "Anything UNCLEAR": "",
}
[/CONTENT]
""",
    },
    "markdown": {
        "PROMPT_TEMPLATE": """
# Context
## Original Requirements
{requirements}

## Search Information
{search_information}

## mermaid quadrantChart code syntax example. DONT USE QUOTO IN CODE DUE TO INVALID SYNTAX. Replace the <Campain X> with REAL COMPETITOR NAME
```mermaid
quadrantChart
    title Reach and engagement of campaigns
    x-axis Low Reach --> High Reach
    y-axis Low Engagement --> High Engagement
    quadrant-1 We should expand
    quadrant-2 Need to promote
    quadrant-3 Re-evaluate
    quadrant-4 May be improved
    "Campaign: A": [0.3, 0.6]
    "Campaign B": [0.45, 0.23]
    "Campaign C": [0.57, 0.69]
    "Campaign D": [0.78, 0.34]
    "Campaign E": [0.40, 0.34]
    "Campaign F": [0.35, 0.78]
    "Our Target Product": [0.5, 0.6]
```

## Format example
{format_example}
-----
Role: You are a professional product manager; the goal is to design a concise, usable, efficient product
Language: Please use the same language as the user requirement to answer, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
Requirements: According to the context, fill in the following missing information, note that each sections are returned in Python code triple quote form seperatedly.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. AND '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote. Output carefully referenced "Format example" in format.

## Language: Provide as Plain text, use the same language as the user requirement.

## Original Requirements: Provide as Plain text, place the polished complete original requirements here

## Product Goals: Provided as Python list[str], up to 3 clear, orthogonal product goals.

## User Stories: Provided as Python list[str], up to 5 scenario-based user stories

## Competitive Analysis: Provided as Python list[str], up to 7 competitive product analyses, consider as similar competitors as possible

## Competitive Quadrant Chart: Use mermaid quadrantChart code syntax. up to 14 competitive products. Translation: Distribute these competitor scores evenly between 0 and 1, trying to conform to a normal distribution centered around 0.5 as much as possible.

## Requirement Analysis: Provide as Plain text.

## Requirement Pool: Provided as Python list[list[str], the parameters are requirement description, priority(P0/P1/P2), respectively, comply with PEP standards

## UI Design draft: Provide as Plain text. Be simple. Describe the elements and functions, also provide a simple style description and layout description.
## Anything UNCLEAR: Provide as Plain text. Try to clarify it.
""",
        "FORMAT_EXAMPLE": """
---
## Original Requirements
The user ... 

## Product Goals
```python
[
    "Create a ...",
]
```

## User Stories
```python
[
    "As a user, ...",
]
```

## Competitive Analysis
```python
[
    "Python Snake Game: ...",
]
```

## Competitive Quadrant Chart
```mermaid
quadrantChart
    title Reach and engagement of campaigns
    ...
    "Our Target Product": [0.6, 0.7]
```

## Requirement Analysis
The product should be a ...

## Requirement Pool
```python
[
    ["End game ...", "P0"]
]
```

## UI Design draft
Give a basic function description, and a draft

## Anything UNCLEAR
There are no unclear points.
---
""",
    },
}

OUTPUT_MAPPING = {
    "Language": (str, ...),
    "Original Requirements": (str, ...),
    "Product Goals": (List[str], ...),
    "User Stories": (List[str], ...),
    "Competitive Analysis": (List[str], ...),
    "Competitive Quadrant Chart": (str, ...),
    "Requirement Analysis": (str, ...),
    "Requirement Pool": (List[List[str]], ...),
    "UI Design draft": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


class WritePRD(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, requirements, format=CONFIG.prompt_format, *args, **kwargs) -> ActionOutput:
        sas = SearchAndSummarize()
        # rsp = await sas.run(context=requirements, system_text=SEARCH_AND_SUMMARIZE_SYSTEM_EN_US)
        rsp = ""
        info = f"### Search Results\n{sas.result}\n\n### Search Summary\n{rsp}"
        if sas.result:
            logger.info(sas.result)
            logger.info(rsp)

        # logger.info(format)
        prompt_template, format_example = get_template(templates, format)
        # logger.info(prompt_template)
        # logger.info(format_example)
        prompt = prompt_template.format(
            requirements=requirements, search_information=info, format_example=format_example
        )
        # logger.info(prompt)
        # prd = await self._aask_v1(prompt, "prd", OUTPUT_MAPPING)
        prd = await self._aask_v1(prompt, "prd", OUTPUT_MAPPING, format=format)
        return prd
