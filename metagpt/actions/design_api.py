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
from metagpt.const import PRDS_FILE_REPO, SYSTEM_DESIGN_FILE_REPO, WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.schema import Document, Documents
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.utils.mermaid import mermaid_to_file

templates = {
    "json": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are an architect; the goal is to design a SOTA PEP8-compliant python system; make the best use of good open source tools
Requirement: Fill in the following missing information based on the context, each section name is a key in json
Max Output: 8192 chars or 2048 tokens. Try to use them up.

## Implementation approach: Provide as Plain text. Analyze the difficult points of the requirements, select the appropriate open-source framework.

## Python package name: Provide as Python str with python triple quoto, concise and clear, characters only use a combination of all lowercase and underscores

## File list: Provided as Python list[str], the list of ONLY REQUIRED files needed to write the program(LESS IS MORE!). Only need relative paths, comply with PEP8 standards. ALWAYS write a main.py or app.py here

## Data structures and interface definitions: Use mermaid classDiagram code syntax, including classes (INCLUDING __init__ method) and functions (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Program call flow: Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.

## Anything UNCLEAR: Provide as Plain text. Make clear here.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": """
[CONTENT]
{
    "Implementation approach": "We will ...",
    "Python package name": "snake_game",
    "File list": ["main.py"],
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
Requirement: Fill in the following missing information based on the context, note that all sections are response with code form separately
Max Output: 8192 chars or 2048 tokens. Try to use them up.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Implementation approach: Provide as Plain text. Analyze the difficult points of the requirements, select the appropriate open-source framework.

## Python package name: Provide as Python str with python triple quoto, concise and clear, characters only use a combination of all lowercase and underscores

## File list: Provided as Python list[str], the list of ONLY REQUIRED files needed to write the program(LESS IS MORE!). Only need relative paths, comply with PEP8 standards. ALWAYS write a main.py or app.py here

## Data structures and interface definitions: Use mermaid classDiagram code syntax, including classes (INCLUDING __init__ method) and functions (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Program call flow: Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.

## Anything UNCLEAR: Provide as Plain text. Make clear here.

""",
        "FORMAT_EXAMPLE": """
---
## Implementation approach
We will ...

## Python package name
```python
"snake_game"
```

## File list
```python
[
    "main.py",
]
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

## Anything UNCLEAR
The requirement is clear to me.
---
""",
    },
}

OUTPUT_MAPPING = {
    "Implementation approach": (str, ...),
    "Python package name": (str, ...),
    "File list": (List[str], ...),
    "Data structures and interface definitions": (str, ...),
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
        self.recreate_workspace(workspace)
        docs_path = workspace / "docs"
        resources_path = workspace / "resources"
        docs_path.mkdir(parents=True, exist_ok=True)
        resources_path.mkdir(parents=True, exist_ok=True)
        await self._save_prd(docs_path, resources_path, context)
        await self._save_system_design(docs_path, resources_path, system_design)

    async def run(self, with_messages, format=CONFIG.prompt_format):
        # 通过git diff来识别docs/prds下哪些PRD文档发生了变动
        prds_file_repo = CONFIG.git_repo.new_file_repository(PRDS_FILE_REPO)
        changed_prds = prds_file_repo.changed_files
        # 通过git diff来识别docs/system_designs下那些设计文档发生了变动；
        system_design_file_repo = CONFIG.git_repo.new_file_repository(SYSTEM_DESIGN_FILE_REPO)
        changed_system_designs = system_design_file_repo.changed_files

        # 对于那些发生变动的PRD和设计文档，重新生成设计内容；
        changed_files = Documents()
        for filename in changed_prds.keys():
            prd = await prds_file_repo.get(filename)
            old_system_design_doc = await system_design_file_repo.get(filename)
            if not old_system_design_doc:
                system_design = await self._run(context=prd.content)
                doc = Document(
                    root_path=SYSTEM_DESIGN_FILE_REPO, filename=filename, content=system_design.instruct_content.json()
                )
            else:
                doc = await self._merge(prd_doc=prd, system_design_doc=old_system_design_doc)
            await system_design_file_repo.save(
                filename=filename, content=doc.content, dependencies={prd.root_relative_path}
            )
            changed_files.docs[filename] = doc

        for filename in changed_system_designs.keys():
            if filename in changed_files.docs:
                continue
            prd_doc = await prds_file_repo.get(filename=filename)
            old_system_design_doc = await system_design_file_repo.get(filename)
            new_system_design_doc = await self._merge(prd_doc, old_system_design_doc)
            await system_design_file_repo.save(
                filename=filename, content=new_system_design_doc.content, dependencies={prd_doc.root_relative_path}
            )
            changed_files.docs[filename] = new_system_design_doc

        # 等docs/system_designs/下所有文件都处理完才发publish message，给后续做全局优化留空间。
        return ActionOutput(content=changed_files.json(), instruct_content=changed_files)

    async def _run(self, context, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)
        # system_design = await self._aask(prompt)
        system_design = await self._aask_v1(prompt, "system_design", OUTPUT_MAPPING, format=format)
        # fix Python package name, we can't system_design.instruct_content.python_package_name = "xxx" since "Python package name" contain space, have to use setattr
        setattr(
            system_design.instruct_content,
            "Python package name",
            system_design.instruct_content.dict()["Python package name"].strip().strip("'").strip('"'),
        )
        await self._rename_workspace(system_design)
        return system_design

    async def _merge(self, prd_doc, system_design_doc):
        return system_design_doc

    async def _rename_workspace(self, system_design):
        if CONFIG.WORKDIR:  # 已经指定了在旧版本上更新
            return

        if isinstance(system_design, ActionOutput):
            ws_name = system_design.instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=system_design)
        CONFIG.git_repo.rename_root(ws_name)
