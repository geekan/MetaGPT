from typing import List, Union

from metagpt.actions import Refine, ActionOutput, SearchAndSummarize
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.utils.get_template import get_template

increment_template = {
    "json": {
        "PROMPT_TEMPLATE": """
# Context
## User's Incremental Requirements
{new_requirements}

## Legacy PRD
{legacy}

## Search Information
{search_information}

## Format example
{format_example}
-----
Role: You are a professional Product Manager tasked with overseeing incremental development and crafting Product Requirements Documents (PRDs) for a concise, usable, and efficient product.
Requirements: According to the context, fill in the following missing information, each section name is a key in json ,If the requirements are unclear, ensure minimum viability and avoid excessive designOnly output one json, nothing else.

## Incremental Requirements: Provide as str, the foremost incremental requirements for PRD here based on the previous.

## Difference Description: Provide as str, the foremost differences description for PRD here based on the previous.

## Incremental Development Plan: Provide as Python list[str], up to 5 clear, incremental development plans. If the requirement itself is simple, the incremental development plan should also be simple

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": """
[CONTENT]
{
    "Incremental Requirements": "",
    "Difference Description": [],
    "Incremental Development Plan": [],
}
[/CONTENT]
""",
    },
    "markdown": {
        "PROMPT_TEMPLATE": """
# Context
You need to refine the requirements based on the Incremental Requirements and the existing requirements' output.
## User's Incremental Requirements
{new_requirements}

## Legacy PRD
{legacy}

## Search Information
{search_information}

## Format example
{format_example}
-----
Role: You are a professional Product Manager tasked with overseeing incremental development and crafting Product Requirements Documents (PRDs) for a concise, usable, and efficient product.
Requirements: According to the context, fill in the following missing information, note that each sections are returned in Python code triple quote form seperatedly. If the requirements are unclear, ensure minimum viability and avoid excessive design
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. AND '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote. Output carefully referenced "Format example" in format.Only output one json, nothing else.

## Incremental Requirements: Provide as str, the foremost incremental requirements for PRD here based on the previous.

## Difference Description: Provide as str, the foremost differences description for PRD here based on the previous.

## Incremental Development Plan: Provide as Python list[str], up to 5 clear, incremental development plans. If the requirement itself is simple, the incremental development plan should also be simple
""",
        "FORMAT_EXAMPLE": """
---
## Incremental Requirements
The boss ...

## Difference Description
...

## Incremental Development Plan
[
    "...",
]
""",
    },
}

INCREMENT_OUTPUT_MAPPING = {
    "Incremental Requirements": (str, ...),
    "Difference Description": (Union[List[str], str], ...),
    "Incremental Development Plan": (List[str], ...),
}


class RefinePRD(Refine):

    def __init__(self, name="RefinePRD", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, new_requirements, legacy, format=CONFIG.prompt_format, *args, **kwargs):
        sas = SearchAndSummarize()
        rsp = ""
        info = f"### Search Results\n{sas.result}\n\n### Search Summary\n{rsp}"
        if sas.result:
            logger.info(sas.result)
            logger.info(rsp)

        prompt_template, format_example = get_template(increment_template, format)
        prompt = prompt_template.format(
            new_requirements=new_requirements, legacy=legacy, search_information=info,
            format_example=format_example
        )
        logger.debug(prompt)
        prd = await self._aask_v1(prompt, "prd", INCREMENT_OUTPUT_MAPPING, format=format)
        return prd
