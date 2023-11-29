#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:26
@Author  : alexanderwu
@File    : design_api.py
@Modified By: mashenquan, 2023/11/27.
            1. According to Section 2.2.3.1 of RFC 135, replace file data in the message with the file name.
            2. According to the design in Section 2.2.3.5.3 of RFC 135, add incremental iteration functionality.
"""
import json
from pathlib import Path
from typing import List

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.const import (
    DATA_API_DESIGN_FILE_REPO,
    PRDS_FILE_REPO,
    SEQ_FLOW_FILE_REPO,
    SYSTEM_DESIGN_FILE_REPO,
    SYSTEM_DESIGN_PDF_FILE_REPO,
)
from metagpt.logs import logger
from metagpt.schema import Document, Documents
from metagpt.utils.common import CodeParser
from metagpt.utils.file_repository import FileRepository
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

MERGE_PROMPT = """
## Old Design
{old_design}

## Context
{context}

-----
Role: You are an architect; The goal is to incrementally update the "Old Design" based on the information provided by the "Context," aiming to design a SOTA PEP8-compliant python system; make the best use of good open source tools
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
Requirement: Fill in the following missing information based on the context, note that all sections are response with code form separately
ATTENTION: Output carefully referenced "Old Design" in format.

## Implementation approach: Provide as Plain text. Analyze the difficult points of the requirements, select the appropriate open-source framework.

## project_name: Provide as Plain text, concise and clear, characters only use a combination of all lowercase and underscores

## File list: Provided as Python list[str], the list of code files (including HTML & CSS IF NEEDED) to write the program. Only need relative paths. ALWAYS write a main.py or app.py here

## Data structures and interfaces: Use mermaid classDiagram code syntax, including classes (INCLUDING __init__ method) and functions (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Program call flow: Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.

## Anything UNCLEAR: Provide as Plain text. Try to clarify it.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like "Old Design" format,
and only output the json inside this tag, nothing else
"""


class WriteDesign(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = (
            "Based on the PRD, think about the system design, and design the corresponding APIs, "
            "data structures, library tables, processes, and paths. Please provide your design, feedback "
            "clearly and in detail."
        )

    async def run(self, with_messages, format=CONFIG.prompt_format):
        # Use `git diff` to identify which PRD documents have been modified in the `docs/prds` directory.
        prds_file_repo = CONFIG.git_repo.new_file_repository(PRDS_FILE_REPO)
        changed_prds = prds_file_repo.changed_files
        # Use `git diff` to identify which design documents in the `docs/system_designs` directory have undergone
        # changes.
        system_design_file_repo = CONFIG.git_repo.new_file_repository(SYSTEM_DESIGN_FILE_REPO)
        changed_system_designs = system_design_file_repo.changed_files

        # For those PRDs and design documents that have undergone changes, regenerate the design content.
        changed_files = Documents()
        for filename in changed_prds.keys():
            doc = await self._update_system_design(
                filename=filename, prds_file_repo=prds_file_repo, system_design_file_repo=system_design_file_repo
            )
            changed_files.docs[filename] = doc

        for filename in changed_system_designs.keys():
            if filename in changed_files.docs:
                continue
            doc = await self._update_system_design(
                filename=filename, prds_file_repo=prds_file_repo, system_design_file_repo=system_design_file_repo
            )
            changed_files.docs[filename] = doc
        if not changed_files.docs:
            logger.info("Nothing has changed.")
        # Wait until all files under `docs/system_designs/` are processed before sending the publish message,
        # leaving room for global optimization in subsequent steps.
        return ActionOutput(content=changed_files.json(), instruct_content=changed_files)

    # =======
    # def recreate_workspace(self, workspace: Path):
    #     try:
    #         shutil.rmtree(workspace)
    #     except FileNotFoundError:
    #         pass  # Folder does not exist, but we don't care
    #     workspace.mkdir(parents=True, exist_ok=True)

    # async def _save_prd(self, docs_path, resources_path, context):
    #     prd_file = docs_path / "prd.md"
    #     if context[-1].instruct_content and context[-1].instruct_content.dict()["Competitive Quadrant Chart"]:
    #         quadrant_chart = context[-1].instruct_content.dict()["Competitive Quadrant Chart"]
    #         await mermaid_to_file(quadrant_chart, resources_path / "competitive_analysis")
    #
    #     if context[-1].instruct_content:
    #         logger.info(f"Saving PRD to {prd_file}")
    #         prd_file.write_text(context[-1].instruct_content.json(ensure_ascii=False), encoding='utf-8')

    # async def _save_system_design(self, docs_path, resources_path, system_design):
    #     data_api_design = system_design.instruct_content.dict()[
    #         "Data structures and interfaces"
    #     ]  # CodeParser.parse_code(block="Data structures and interfaces", text=content)
    #     seq_flow = system_design.instruct_content.dict()[
    #         "Program call flow"
    #     ]  # CodeParser.parse_code(block="Program call flow", text=content)
    #     await mermaid_to_file(data_api_design, resources_path / "data_api_design")
    #     await mermaid_to_file(seq_flow, resources_path / "seq_flow")
    #     system_design_file = docs_path / "system_design.md"
    #     logger.info(f"Saving System Designs to {system_design_file}")
    #     system_design_file.write_text(system_design.instruct_content.json(ensure_ascii=False), encoding='utf-8')

    # async def _save(self, context, system_design):
    #     if isinstance(system_design, ActionOutput):
    #         project_name = system_design.instruct_content.dict()["project_name"]
    #     else:
    #         project_name = CodeParser.parse_str(block="project_name", text=system_design)
    #     workspace = CONFIG.workspace_path / project_name
    #     self.recreate_workspace(workspace)
    #     docs_path = workspace / "docs"
    #     resources_path = workspace / "resources"
    #     docs_path.mkdir(parents=True, exist_ok=True)
    #     resources_path.mkdir(parents=True, exist_ok=True)
    #     await self._save_prd(docs_path, resources_path, context)
    #     await self._save_system_design(docs_path, resources_path, system_design)

    #    async def run(self, context, format=CONFIG.prompt_format):

    async def _new_system_design(self, context, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)
        # system_design = await self._aask(prompt)
        system_design = await self._aask_v1(prompt, "system_design", OUTPUT_MAPPING, format=format)

        # fix project_name, we can't system_design.instruct_content.python_package_name = "xxx" since "project_name"
        # contain space, have to use setattr
        self._rename_project_name(system_design=system_design)
        await self._rename_workspace(system_design)
        # =======
        #         # fix project_name, we can't system_design.instruct_content.python_package_name = "xxx" since "project_name" contain space, have to use setattr
        #         # setattr(
        #         #     system_design.instruct_content,
        #         #     "project_name",
        #         #     system_design.instruct_content.dict()["project_name"].strip().strip("'").strip('"'),
        #         # )
        #         await self._save(context, system_design)
        # >>>>>>> feature/geekan_cli_etc
        return system_design

    async def _merge(self, prd_doc, system_design_doc, format=CONFIG.prompt_format):
        prompt = MERGE_PROMPT.format(old_design=system_design_doc.content, context=prd_doc.content)
        system_design = await self._aask_v1(prompt, "system_design", OUTPUT_MAPPING, format=format)
        # fix Python package name, we can't system_design.instruct_content.python_package_name = "xxx" since "Python
        # package name" contain space, have to use setattr
        self._rename_project_name(system_design=system_design)
        system_design_doc.content = system_design.instruct_content.json(ensure_ascii=False)
        return system_design_doc

    @staticmethod
    def _rename_project_name(system_design):
        if CONFIG.project_name:
            setattr(
                system_design.instruct_content,
                "project_name",
                CONFIG.project_name,
            )
            return
        setattr(
            system_design.instruct_content,
            "project_name",
            system_design.instruct_content.dict()["project_name"].strip().strip("'").strip('"'),
        )

    @staticmethod
    async def _rename_workspace(system_design):
        if CONFIG.project_path:  # Updating on the old version has already been specified if it's valid. According to
            # Section 2.2.3.10 of RFC 135
            return

        if isinstance(system_design, ActionOutput):
            ws_name = system_design.instruct_content.dict()["project_name"]
        else:
            ws_name = CodeParser.parse_str(block="project_name", text=system_design)
        CONFIG.git_repo.rename_root(ws_name)

    async def _update_system_design(self, filename, prds_file_repo, system_design_file_repo) -> Document:
        prd = await prds_file_repo.get(filename)
        old_system_design_doc = await system_design_file_repo.get(filename)
        if not old_system_design_doc:
            system_design = await self._new_system_design(context=prd.content)
            doc = Document(
                root_path=SYSTEM_DESIGN_FILE_REPO,
                filename=filename,
                content=system_design.instruct_content.json(ensure_ascii=False),
            )
        else:
            doc = await self._merge(prd_doc=prd, system_design_doc=old_system_design_doc)
        await system_design_file_repo.save(
            filename=filename, content=doc.content, dependencies={prd.root_relative_path}
        )
        await self._save_data_api_design(doc)
        await self._save_seq_flow(doc)
        await self._save_pdf(doc)
        return doc

    @staticmethod
    async def _save_data_api_design(design_doc):
        m = json.loads(design_doc.content)
        data_api_design = m.get("Data structures and interface definitions")
        if not data_api_design:
            return
        pathname = CONFIG.git_repo.workdir / Path(DATA_API_DESIGN_FILE_REPO) / Path(design_doc.filename).with_suffix("")
        await WriteDesign._save_mermaid_file(data_api_design, pathname)
        logger.info(f"Save class view to {str(pathname)}")

    @staticmethod
    async def _save_seq_flow(design_doc):
        m = json.loads(design_doc.content)
        seq_flow = m.get("Program call flow")
        if not seq_flow:
            return
        pathname = CONFIG.git_repo.workdir / Path(SEQ_FLOW_FILE_REPO) / Path(design_doc.filename).with_suffix("")
        await WriteDesign._save_mermaid_file(seq_flow, pathname)
        logger.info(f"Saving sequence flow to {str(pathname)}")

    @staticmethod
    async def _save_pdf(design_doc):
        await FileRepository.save_as(doc=design_doc, with_suffix=".md", relative_path=SYSTEM_DESIGN_PDF_FILE_REPO)

    @staticmethod
    async def _save_mermaid_file(data: str, pathname: Path):
        pathname.parent.mkdir(parents=True, exist_ok=True)
        await mermaid_to_file(data, pathname)
