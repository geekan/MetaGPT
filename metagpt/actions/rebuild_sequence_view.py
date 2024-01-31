#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4
@Author  : mashenquan
@File    : rebuild_sequence_view.py
@Desc    : Rebuild sequence view info
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions import Action
from metagpt.config2 import config
from metagpt.const import GRAPH_REPO_FILE_REPO
from metagpt.logs import logger
from metagpt.repo_parser import CodeBlockInfo, DotClassInfo
from metagpt.schema import UMLClassView
from metagpt.utils.common import (
    add_affix,
    aread,
    auto_namespace,
    concat_namespace,
    general_after_log,
    list_files,
    parse_json_code_block,
    read_file_block,
    split_namespace,
)
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.graph_repository import SPO, GraphKeyword, GraphRepository


class SQVUseCase(BaseModel):
    description: str
    inputs: List[str]
    outputs: List[str]
    actors: List[str]
    steps: List[str]
    reason: str


class SQVUseCaseDetails(BaseModel):
    description: str
    use_cases: List[SQVUseCase]
    relationship: List[str]


class RebuildSequenceView(Action):
    graph_db: Optional[GraphRepository] = None

    async def run(self, with_messages=None, format=config.prompt_schema):
        graph_repo_pathname = self.context.git_repo.workdir / GRAPH_REPO_FILE_REPO / self.context.git_repo.workdir.name
        self.graph_db = await DiGraphRepository.load_from(str(graph_repo_pathname.with_suffix(".json")))
        entries = await self._search_main_entry()
        for entry in entries:
            await self._rebuild_main_sequence_view(entry)
            while await self._merge_sequence_view(entry):
                pass
        await self.graph_db.save()

    # @retry(
    #     wait=wait_random_exponential(min=1, max=20),
    #     stop=stop_after_attempt(6),
    #     after=general_after_log(logger),
    # )
    async def _rebuild_main_sequence_view(self, entry):
        filename = entry.subject.split(":", 1)[0]
        rows = await self.graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)
        classes = []
        prefix = filename + ":"
        for r in rows:
            if prefix in r.subject:
                classes.append(r)
                await self._rebuild_use_case(r.subject)
        participants = set()
        class_details = []
        class_views = []
        for c in classes:
            detail = await self._get_class_detail(c.subject)
            if not detail:
                continue
            class_details.append(detail)
            view = await self._get_uml_class_view(c.subject)
            if view:
                class_views.append(view)

            actors = await self._get_participants(c.subject)
            participants.update(set(actors))

        use_case_blocks = []
        for c in classes:
            use_cases = await self._get_class_use_cases(c.subject)
            use_case_blocks.extend(use_cases)
        prompt_blocks = ["## Use Cases\n" + "\n".join(use_case_blocks)]
        block = "## Participants\n"
        for p in participants:
            block += f"- {p}\n"
        prompt_blocks.append(block)
        block = "## Mermaid Class Views\n```mermaid\n"
        block += "\n\n".join([c.get_mermaid() for c in class_views])
        block += "\n```\n"
        prompt_blocks.append(block)
        block = "## Source Code\n```python\n"
        block += await self._get_source_code(filename)
        block += "\n```\n"
        prompt_blocks.append(block)
        prompt = "\n---\n".join(prompt_blocks)

        rsp = await self.llm.aask(
            msg=prompt,
            system_msgs=[
                "You are a python code to Mermaid Sequence Diagram translator in function detail.",
                "Translate the given markdown text to a Mermaid Sequence Diagram.",
                "Return the merged Mermaid sequence diagram in a markdown code block format.",
            ],
        )
        sequence_view = rsp.removeprefix("```mermaid").removesuffix("```")
        rows = await self.graph_db.select(subject=entry.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW)
        for r in rows:
            await self.graph_db.delete(subject=r.subject, predicate=r.predicate, object_=r.object_)
        await self.graph_db.insert(
            subject=entry.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW, object_=sequence_view
        )
        await self.graph_db.insert(
            subject=entry.subject,
            predicate=GraphKeyword.HAS_SEQUENCE_VIEW_VER,
            object_=concat_namespace(datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3], add_affix(sequence_view)),
        )
        for c in classes:
            await self.graph_db.insert(
                subject=entry.subject, predicate=GraphKeyword.HAS_PARTICIPANT, object_=auto_namespace(c.subject)
            )
        await self.graph_db.save()

    async def _merge_sequence_view(self, entry) -> bool:
        new_participant = await self._search_new_participant(entry)
        if not new_participant:
            return False

        await self._merge_participant(entry, new_participant)
        return True

    async def _search_main_entry(self) -> List:
        rows = await self.graph_db.select(predicate=GraphKeyword.HAS_PAGE_INFO)
        tag = "__name__:__main__"
        entries = []
        for r in rows:
            if tag in r.subject or tag in r.object_:
                entries.append(r)
        return entries

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _rebuild_use_case(self, ns_class_name):
        rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_USE_CASE)
        if rows:
            return

        detail = await self._get_class_detail(ns_class_name)
        if not detail:
            return
        participants = set()
        participants.update(set(detail.compositions))
        participants.update(set(detail.aggregations))
        class_view = await self._get_uml_class_view(ns_class_name)
        source_code = await self._get_source_code(ns_class_name)

        prompt_blocks = []
        block = "## Participants\n"
        for p in participants:
            block += f"- {p}\n"
        prompt_blocks.append(block)
        block = "## Mermaid Class Views\n```mermaid\n"
        block += class_view.get_mermaid()
        block += "\n```\n"
        prompt_blocks.append(block)
        block = "## Source Code\n```python\n"
        block += source_code
        block += "\n```\n"
        prompt_blocks.append(block)
        prompt = "\n---\n".join(prompt_blocks)

        rsp = await self.llm.aask(
            msg=prompt,
            system_msgs=[
                "You are a python code to UML 2.0 Use Case translator.",
                'The generated UML 2.0 Use Case must include the roles or entities listed in "Participants".',
                'The functional descriptions of Actors and Use Cases in the generated UML 2.0 Use Case must not conflict with the information in "Mermaid Class Views".',
                # 'Only steps that involve input, output, and interactive operations with the external system at the same time can be considered as independent use cases.',
                # "Only steps that involve input, output, and interactive operations with the external system at the same time can be considered as independent use cases, steps that do not meet any one condition should be incorporated into other use cases.",
                'The section under `if __name__ == "__main__":` of "Source Code" contains information about external system interactions with the internal system.',
                "Return a markdown JSON object with:\n"
                '- a "description" key to explain what the whole source code want to do;\n'
                '- a "use_cases" key list all use cases, each use case in the list should including a `description` key describes about what the use case to do, a `inputs` key lists the input names of the use case from external sources, a `outputs` key lists the output names of the use case to external sources, a `actors` key lists the participant actors of the use case, a `steps` key lists the steps about how the use case works step by step, a `reason` key explaining under what circumstances would the external system execute this use case.\n'
                '- a "relationship" key lists all the descriptions of relationship among these use cases.\n',
            ],
        )

        code_blocks = parse_json_code_block(rsp)
        for block in code_blocks:
            detail = SQVUseCaseDetails.model_validate_json(block)
            await self.graph_db.insert(
                subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_USE_CASE, object_=detail.model_dump_json()
            )
        await self.graph_db.save()

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _rebuild_sequence_view(self, ns_class_name):
        await self._rebuild_use_case(ns_class_name)

        prompts_blocks = []
        use_case_markdown = await self._get_class_use_cases(ns_class_name)
        if not use_case_markdown:  # external class
            await self.graph_db.insert(subject=ns_class_name, predicate=GraphKeyword.HAS_SEQUENCE_VIEW, object_="")
            await self.graph_db.save()
            return
        block = f"## Use Cases\n{use_case_markdown}"
        prompts_blocks.append(block)

        participants = await self._get_participants(ns_class_name)
        block = "## Participants\n" + "\n".join([f"- {s}" for s in participants])
        prompts_blocks.append(block)

        view = await self._get_uml_class_view(ns_class_name)
        block = "## Mermaid Class Views\n```mermaid\n"
        block += view.get_mermaid()
        block += "\n```\n"
        prompts_blocks.append(block)

        block = "## Source Code\n```python\n"
        block += await self._get_source_code(ns_class_name)
        block += "\n```\n"
        prompts_blocks.append(block)
        prompt = "\n---\n".join(prompts_blocks)

        rsp = await self.llm.aask(
            prompt,
            system_msgs=[
                "You are a Mermaid Sequence Diagram translator in function detail.",
                "Translate the markdown text to a Mermaid Sequence Diagram.",
                "Return a markdown mermaid code block.",
            ],
        )

        sequence_view = rsp.removeprefix("```mermaid").removesuffix("```")
        await self.graph_db.insert(
            subject=ns_class_name, predicate=GraphKeyword.HAS_SEQUENCE_VIEW, object_=sequence_view
        )
        await self.graph_db.save()

    async def _get_participants(self, ns_class_name) -> List[str]:
        participants = set()
        detail = await self._get_class_detail(ns_class_name)
        if not detail:
            return []
        participants.update(set(detail.compositions))
        participants.update(set(detail.aggregations))
        return list(participants)

    async def _get_class_use_cases(self, ns_class_name) -> str:
        block = ""
        rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_USE_CASE)
        for i, r in enumerate(rows):
            detail = SQVUseCaseDetails.model_validate_json(r.object_)
            block += f"\n### {i + 1}. {detail.description}"
            for j, use_case in enumerate(detail.use_cases):
                block += f"\n#### {i + 1}.{j + 1}. {use_case.description}\n"
                block += "\n##### Inputs\n" + "\n".join([f"- {s}" for s in use_case.inputs])
                block += "\n##### Outputs\n" + "\n".join([f"- {s}" for s in use_case.outputs])
                block += "\n##### Actors\n" + "\n".join([f"- {s}" for s in use_case.actors])
                block += "\n##### Steps\n" + "\n".join([f"- {s}" for s in use_case.steps])
            block += "\n#### Use Case Relationship\n" + "\n".join([f"- {s}" for s in detail.relationship])
        return block + "\n"

    async def _get_class_detail(self, ns_class_name) -> DotClassInfo | None:
        rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_DETAIL)
        if not rows:
            return None
        dot_class_info = DotClassInfo.model_validate_json(rows[0].object_)
        return dot_class_info

    async def _get_uml_class_view(self, ns_class_name) -> UMLClassView | None:
        rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_VIEW)
        if not rows:
            return None
        class_view = UMLClassView.model_validate_json(rows[0].object_)
        return class_view

    async def _get_source_code(self, ns_class_name) -> str:
        rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_PAGE_INFO)
        filename = split_namespace(ns_class_name=ns_class_name)[0]
        if not rows:
            src_filename = RebuildSequenceView._get_full_filename(root=self.i_context, pathname=filename)
            if not src_filename:
                return ""
            return await aread(filename=src_filename, encoding="utf-8")
        code_block_info = CodeBlockInfo.model_validate_json(rows[0].object_)
        return await read_file_block(
            filename=filename, lineno=code_block_info.lineno, end_lineno=code_block_info.end_lineno
        )

    @staticmethod
    def _get_full_filename(root: str | Path, pathname: str | Path) -> Path | None:
        files = list_files(root=root)
        postfix = "/" + str(pathname)
        for i in files:
            if str(i).endswith(postfix):
                return i
        return None

    @staticmethod
    def parse_participant(mermaid_sequence_diagram: str) -> List[str]:
        pattern = r"participant ([a-zA-Z\.0-9_]+)"
        matches = re.findall(pattern, mermaid_sequence_diagram)
        return matches

    async def _search_new_participant(self, entry: SPO) -> str | None:
        rows = await self.graph_db.select(subject=entry.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW)
        if not rows:
            return None
        sequence_view = rows[0].object_
        rows = await self.graph_db.select(subject=entry.subject, predicate=GraphKeyword.HAS_PARTICIPANT)
        merged_participants = []
        for r in rows:
            name = split_namespace(r.object_)[-1]
            merged_participants.append(name)
        participants = self.parse_participant(sequence_view)
        for p in participants:
            if p in merged_participants:
                continue
            return p
        return None

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _merge_participant(self, entry: SPO, class_name: str):
        rows = await self.graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)
        participants = []
        for r in rows:
            name = split_namespace(r.subject)[-1]
            if name == class_name:
                participants.append(r)
        if len(participants) == 0:  # external participants
            await self.graph_db.insert(
                subject=entry.subject, predicate=GraphKeyword.HAS_PARTICIPANT, object_=concat_namespace("?", class_name)
            )
            await self.graph_db.save()
            return
        if len(participants) > 1:
            for r in participants:
                await self.graph_db.insert(
                    subject=entry.subject, predicate=GraphKeyword.HAS_PARTICIPANT, object_=auto_namespace(r.subject)
                )
            await self.graph_db.save()
            return

        participant = participants[0]
        await self._rebuild_sequence_view(participant.subject)
        sequence_views = await self.graph_db.select(
            subject=participant.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW
        )
        if not sequence_views:  # external class
            return
        rows = await self.graph_db.select(subject=entry.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW)
        prompt = f"```mermaid\n{sequence_views[0].object_}\n```\n---\n```mermaid\n{rows[0].object_}\n```"

        rsp = await self.llm.aask(
            prompt,
            system_msgs=[
                "You are a tool to merge sequence diagrams into one.",
                "Participants with the same name are considered identical.",
                "Return the merged Mermaid sequence diagram in a markdown code block format.",
            ],
        )

        sequence_view = rsp.removeprefix("```mermaid").removesuffix("```")
        rows = await self.graph_db.select(subject=entry.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW)
        for r in rows:
            await self.graph_db.delete(subject=r.subject, predicate=r.predicate, object_=r.object_)
        await self.graph_db.insert(
            subject=entry.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW, object_=sequence_view
        )
        await self.graph_db.insert(
            subject=entry.subject,
            predicate=GraphKeyword.HAS_SEQUENCE_VIEW_VER,
            object_=concat_namespace(datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3], add_affix(sequence_view)),
        )
        await self.graph_db.insert(
            subject=entry.subject, predicate=GraphKeyword.HAS_PARTICIPANT, object_=auto_namespace(participant.subject)
        )
        await self.graph_db.save()
