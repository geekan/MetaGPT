#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:26
@Author  : alexanderwu
@File    : design_api.py
"""
import shutil
from pathlib import Path
from typing import List

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.mermaid import mermaid_to_file

templates = {
    "json": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are an architect; the goal is to design a SOTA PEP8-compliant python system
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
Requirement: Fill in the following missing information based on the context, each section name is a key in json

## Implementation approach: Provide as Plain text. Analyze the difficult points of the requirements, select appropriate open-source frameworks.

## project_name: Provide as Plain text, concise and clear, characters only use a combination of all lowercase and underscores

## File list: Provided as Python list[str], the list of files needed (including HTML & CSS IF NEEDED) to write the program. Only need relative paths. ALWAYS write a main.py or app.py here

## Data structures and interfaces: Use mermaid classDiagram code syntax, including classes (INCLUDING __init__ method) and functions (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Program call flow: Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.

## Anything UNCLEAR: Provide as Plain text. Try to clarify it.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": """
[CONTENT]
{
    "Implementation approach": "We will ...",
    "project_name": "snake_game",
    "File list": ["main.py"],
    "Data structures and interfaces": '
    classDiagram
        class Game{
            +int score
        }
        ...
        Game "1" -- "1" Food: has
    ',
    "Program call flow": '
    sequenceDiagram
        participant M as Main
        ...
        G->>M: end game
    ',
    "Anything UNCLEAR": "The requirement is clear to me."
}
[/CONTENT]
""",
    },
    "markdown": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are an architect; the goal is to design a SOTA PEP8-compliant python system; make the best use of good open source tools
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
Requirement: Fill in the following missing information based on the context, note that all sections are response with code form separately
ATTENTION: Output carefully referenced "Format example" in format.

## Implementation approach: Provide as Plain text. Analyze the difficult points of the requirements, select the appropriate open-source framework.

## project_name: Provide as Plain text, concise and clear, characters only use a combination of all lowercase and underscores

## File list: Provided as Python list[str], the list of code files (including HTML & CSS IF NEEDED) to write the program. Only need relative paths. ALWAYS write a main.py or app.py here

## Data structures and interfaces: Use mermaid classDiagram code syntax, including classes (INCLUDING __init__ method) and functions (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Program call flow: Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.

## Anything UNCLEAR: Provide as Plain text. Try to clarify it.

""",
        "FORMAT_EXAMPLE": """
---
## Implementation approach
We will ...

## project_name
```python
"snake_game"
```

## File list
```python
[
    "main.py",
]
```

## Data structures and interfaces
```mermaid
classDiagram
    class Game{
        +int score
    }
    ...
    Game "1" -- "1" Food: has
```

## Program call flow
```mermaid
sequenceDiagram
    participant M as Main
    ...
    G->>M: end game
```

## Anything UNCLEAR
The requirement is clear to me.
---
""",
    },
}

OUTPUT_MAPPING = {
    "Implementation approach": (str, ...),
    "project_name": (str, ...),
    "File list": (List[str], ...),
    "Data structures and interfaces": (str, ...),
    "Program call flow": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


class WriteDesign(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = (
            "Based on the PRD, think about the system design, and design the corresponding APIs, "
            "data structures, library tables, processes, and paths. Please provide your design, feedback "
            "clearly and in detail."
        )

    def recreate_workspace(self, workspace: Path):
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass  # Folder does not exist, but we don't care
        workspace.mkdir(parents=True, exist_ok=True)

    async def _save_prd(self, docs_path, resources_path, context):
        prd_file = docs_path / "prd.md"
        if context[-1].instruct_content and context[-1].instruct_content.dict()["Competitive Quadrant Chart"]:
            quadrant_chart = context[-1].instruct_content.dict()["Competitive Quadrant Chart"]
            await mermaid_to_file(quadrant_chart, resources_path / "competitive_analysis")

        if context[-1].instruct_content:
            logger.info(f"Saving PRD to {prd_file}")
            prd_file.write_text(context[-1].instruct_content.json(ensure_ascii=False), encoding='utf-8')

    async def _save_system_design(self, docs_path, resources_path, system_design):
        data_api_design = system_design.instruct_content.dict()[
            "Data structures and interfaces"
        ]  # CodeParser.parse_code(block="Data structures and interfaces", text=content)
        seq_flow = system_design.instruct_content.dict()[
            "Program call flow"
        ]  # CodeParser.parse_code(block="Program call flow", text=content)
        await mermaid_to_file(data_api_design, resources_path / "data_api_design")
        await mermaid_to_file(seq_flow, resources_path / "seq_flow")
        system_design_file = docs_path / "system_design.md"
        logger.info(f"Saving System Designs to {system_design_file}")
        system_design_file.write_text(system_design.instruct_content.json(ensure_ascii=False), encoding='utf-8')

    async def _save(self, context, system_design):
        if isinstance(system_design, ActionOutput):
            project_name = system_design.instruct_content.dict()["project_name"]
        else:
            project_name = CodeParser.parse_str(block="project_name", text=system_design)
        workspace = CONFIG.workspace_path / project_name
        self.recreate_workspace(workspace)
        docs_path = workspace / "docs"
        resources_path = workspace / "resources"
        docs_path.mkdir(parents=True, exist_ok=True)
        resources_path.mkdir(parents=True, exist_ok=True)
        await self._save_prd(docs_path, resources_path, context)
        await self._save_system_design(docs_path, resources_path, system_design)

    async def run(self, context, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)
        # system_design = await self._aask(prompt)
        system_design = await self._aask_v1(prompt, "system_design", OUTPUT_MAPPING, format=format)
        # fix project_name, we can't system_design.instruct_content.python_package_name = "xxx" since "project_name" contain space, have to use setattr
        # setattr(
        #     system_design.instruct_content,
        #     "project_name",
        #     system_design.instruct_content.dict()["project_name"].strip().strip("'").strip('"'),
        # )
        await self._save(context, system_design)
        return system_design
