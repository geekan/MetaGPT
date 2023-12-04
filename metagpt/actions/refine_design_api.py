#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import shutil
from pathlib import Path
from typing import List, Union

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.utils.mermaid import mermaid_to_file

templates = {
    "json": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Legacy
{legacy}

## Format example
{format_example}
-----
Role: You are an architect; the goal is to perform incremental development and design a state-of-the-art (SOTA) PEP8-compliant Python system based on the context and legacy design. Make the best use of good open source tools.
Requirement: Fill in the following missing information based on the context, each section name is a key in json. Output exactly as shown in the example, including single and double quotes.
Max Output: 8192 chars or 2048 tokens. Try to use them up.

## Incremental implementation approach: Provide as Python list[str]. Analyze the difficult points of the requirements, select the appropriate open-source framework. Up to 5.

## Python package name: Provide as Python str with python triple quoto, concise and clear, characters only use a combination of all lowercase and underscores

## Data structures and interface definitions: Use single quotes to wrap content. Use mermaid classDiagram code syntax, including classes (INCLUDING __init__ method) and functions (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Program call flow: Use single quotes to wrap content. Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example.
Output exactly as shown in the example, including single and double quotes, and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": """
[CONTENT]
{
    "Incremental implementation approach": ["We will ...",],
    "Python package name": "new_name",
    "Data structures and interface definitions": '
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
    '
}
[/CONTENT]
""",
    },
    "markdown": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Legacy
{legacy}

## Format example
{format_example}
-----
Role: You are an architect; the goal is to perform incremental development and design a state-of-the-art (SOTA) PEP8-compliant Python system based on the context and legacy design. Make the best use of good open source tools.
Requirement: Fill in the following missing information based on the context, note that all sections are response with code form separately. Output exactly as shown in the example, including single and double quotes.
Max Output: 8192 chars or 2048 tokens. Try to use them up.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Incremental implementation approach: Provide as Python list[str]. Analyze the difficult points of the requirements, select the appropriate open-source framework. Up to 5.

## Python package name: Provide as Python str with python triple quoto, concise and clear, characters only use a combination of all lowercase and underscores

## Data structures and interface definitions: Use single quotes to wrap content. Use mermaid classDiagram code syntax, including classes (INCLUDING __init__ method) and functions (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Program call flow: Use single quotes to wrap content. Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.

""",
        "FORMAT_EXAMPLE": """
---

## Incremental implementation approach
```python
[
    "We will ...",
]
```

## Python package name
```python
"new_name"
```

## Data structures and interface definitions
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
---
""",
    },
}

OUTPUT_MAPPING = {
    # "Incremental Requirements": (str, ...),
    # "Difference Description": (Union[List[str], str], ...),
    "Incremental implementation approach": (Union[List[str], str], ...),
    "Python package name": (str, ...),
    # "File list": (List[str], ...),
    "Data structures and interface definitions": (str, ...),
    "Program call flow": (str, ...)
}


class RefineDesign(Action):
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

    def create_or_increment_workspace(self, workspace: Path):
        # 如果工作空间已存在，添加数字以区分
        original_workspace = workspace
        index = 1
        while workspace.exists():
            ws_name_match = re.match(r'^(.*)_([\d]+)$', original_workspace.name)
            if ws_name_match:
                base_name, existing_index = ws_name_match.groups()
                index = int(existing_index)
                index += 1
                workspace = original_workspace.parent / f"{base_name}_{index}"
            else:
                workspace = original_workspace.parent / f"{original_workspace.name}_{index}"
            index += 1

        # 创建工作空间，包括所有必要的父文件夹
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    async def _save_prd(self, docs_path, resources_path, context):
        prd_file = docs_path / "prd.md"

        if context[-1].instruct_content:
            logger.info(f"Saving PRD to {prd_file}")
            prd_file.write_text(json_to_markdown(context[-1].instruct_content.dict()))

    async def _save_system_design(self, docs_path, resources_path, system_design):
        data_api_design = system_design.instruct_content.dict()[
            "Data structures and interface definitions"
        ]  # CodeParser.parse_code(block="Data structures and interface definitions", text=content)
        seq_flow = system_design.instruct_content.dict()[
            "Program call flow"
        ]  # CodeParser.parse_code(block="Program call flow", text=content)
        await mermaid_to_file(data_api_design, resources_path / "data_api_design")
        await mermaid_to_file(seq_flow, resources_path / "seq_flow")
        system_design_file = docs_path / "system_design.md"
        logger.info(f"Saving System Designs to {system_design_file}")
        system_design_file.write_text((json_to_markdown(system_design.instruct_content.dict())))

    async def _save(self, context, system_design):
        if isinstance(system_design, ActionOutput):
            ws_name = system_design.instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=system_design)
        workspace = WORKSPACE_ROOT / ws_name
        # workspace = self.create_or_increment_workspace(workspace)
        self.recreate_workspace(workspace)
        docs_path = workspace / "docs"
        resources_path = workspace / "resources"
        docs_path.mkdir(parents=True, exist_ok=True)
        resources_path.mkdir(parents=True, exist_ok=True)
        await self._save_prd(docs_path, resources_path, context)
        await self._save_system_design(docs_path, resources_path, system_design)

    async def run(self, context, legacy, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, legacy=legacy, format_example=format_example)
        # system_design = await self._aask(prompt)
        system_design = await self._aask_v1(prompt, "system_design", OUTPUT_MAPPING, format=format)
        # fix Python package name, we can't system_design.instruct_content.python_package_name = "xxx" since "Python package name" contain space, have to use setattr
        setattr(
            system_design.instruct_content,
            "Python package name",
            system_design.instruct_content.dict()["Python package name"].strip().strip("'").strip('"'),
        )
        await self._save(context, system_design)
        return system_design
