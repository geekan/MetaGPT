#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4
@Author  : mashenquan
@File    : rebuild_sequence_view.py
@Desc    : Reconstruct sequence view information through reverse engineering.
    Implement RFC197, https://deepwisdom.feishu.cn/wiki/VyK0wfq56ivuvjklMKJcmHQknGt
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

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


class ReverseUseCase(BaseModel):
    """
    Represents a reverse engineered use case.

    Attributes:
        description (str): A description of the reverse use case.
        inputs (List[str]): List of inputs for the reverse use case.
        outputs (List[str]): List of outputs for the reverse use case.
        actors (List[str]): List of actors involved in the reverse use case.
        steps (List[str]): List of steps for the reverse use case.
        reason (str): The reason behind the reverse use case.
    """

    description: str
    inputs: List[str]
    outputs: List[str]
    actors: List[str]
    steps: List[str]
    reason: str


class ReverseUseCaseDetails(BaseModel):
    """
    Represents details of a reverse engineered use case.

    Attributes:
        description (str): A description of the reverse use case details.
        use_cases (List[ReverseUseCase]): List of reverse use cases.
        relationship (List[str]): List of relationships associated with the reverse use case details.
    """

    description: str
    use_cases: List[ReverseUseCase]
    relationship: List[str]


class RebuildSequenceView(Action):
    """
    Represents an action to reconstruct sequence view through reverse engineering.

    Attributes:
        graph_db (Optional[GraphRepository]): An optional instance of GraphRepository for graph database operations.
    """

    graph_db: Optional[GraphRepository] = None

    async def run(self, with_messages=None, format=config.prompt_schema):
        """
        Implementation of `Action`'s `run` method.

        Args:
            with_messages (Optional[Type]): An optional argument specifying messages to react to.
            format (str): The format for the prompt schema.
        """
        graph_repo_pathname = self.context.git_repo.workdir / GRAPH_REPO_FILE_REPO / self.context.git_repo.workdir.name
        self.graph_db = await DiGraphRepository.load_from(str(graph_repo_pathname.with_suffix(".json")))
        if not self.i_context:
            entries = await self._search_main_entry()
        else:
            entries = [SPO(subject=self.i_context, predicate="", object_="")]
        for entry in entries:
            await self._rebuild_main_sequence_view(entry)
            while await self._merge_sequence_view(entry):
                pass
        await self.graph_db.save()

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _rebuild_main_sequence_view(self, entry: SPO):
        """
        Reconstruct the sequence diagram for the __main__ entry of the source code through reverse engineering.

        Args:
            entry (SPO): The SPO (Subject, Predicate, Object) object in the graph database that is related to the
                subject `__name__:__main__`.
        """
        filename = entry.subject.split(":", 1)[0]
        rows = await self.graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)
        classes = []
        prefix = filename + ":"
        for r in rows:
            if prefix in r.subject:
                classes.append(r)
                await self._rebuild_use_case(r.subject)
        participants = await self._search_participants(split_namespace(entry.subject)[0])
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
            use_case_blocks.append(use_cases)
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
            stream=False,
        )
        sequence_view = rsp.removeprefix("```mermaid").removesuffix("```")
        rows = await self.graph_db.select(subject=entry.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW)
        for r in rows:
            if r.predicate == GraphKeyword.HAS_SEQUENCE_VIEW:
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
        await self._save_sequence_view(subject=entry.subject, content=sequence_view)

    async def _merge_sequence_view(self, entry: SPO) -> bool:
        """
        Augments additional information to the provided SPO (Subject, Predicate, Object) entry in the sequence diagram.

        Args:
            entry (SPO): The SPO object representing the relationship in the graph database.

        Returns:
            bool: True if additional information has been augmented, otherwise False.
        """
        new_participant = await self._search_new_participant(entry)
        if not new_participant:
            return False

        await self._merge_participant(entry, new_participant)
        return True

    async def _search_main_entry(self) -> List:
        """
        Asynchronously searches for the SPO object that is related to `__name__:__main__`.

        Returns:
            List: A list containing information about the main entry in the sequence diagram.
        """
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
    async def _rebuild_use_case(self, ns_class_name: str):
        """
        Asynchronously reconstructs the use case for the provided namespace-prefixed class name.

        Args:
            ns_class_name (str): The namespace-prefixed class name for which the use case is to be reconstructed.
        """
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

        # prompt_blocks = [
        #     "## Instruction\n"
        #     "You are a python code to UML 2.0 Use Case translator.\n"
        #     'The generated UML 2.0 Use Case must include the roles or entities listed in "Participants".\n'
        #     "The functional descriptions of Actors and Use Cases in the generated UML 2.0 Use Case must not "
        #     'conflict with the information in "Mermaid Class Views".\n'
        #     'The section under `if __name__ == "__main__":` of "Source Code" contains information about external '
        #     "system interactions with the internal system.\n"
        # ]
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
                "The functional descriptions of Actors and Use Cases in the generated UML 2.0 Use Case must not "
                'conflict with the information in "Mermaid Class Views".',
                'The section under `if __name__ == "__main__":` of "Source Code" contains information about external '
                "system interactions with the internal system.",
                "Return a markdown JSON object with:\n"
                '- a "description" key to explain what the whole source code want to do;\n'
                '- a "use_cases" key list all use cases, each use case in the list should including a `description` '
                "key describes about what the use case to do, a `inputs` key lists the input names of the use case "
                "from external sources, a `outputs` key lists the output names of the use case to external sources, "
                "a `actors` key lists the participant actors of the use case, a `steps` key lists the steps about how "
                "the use case works step by step, a `reason` key explaining under what circumstances would the "
                "external system execute this use case.\n"
                '- a "relationship" key lists all the descriptions of relationship among these use cases.\n',
            ],
            stream=False,
        )

        code_blocks = parse_json_code_block(rsp)
        for block in code_blocks:
            detail = ReverseUseCaseDetails.model_validate_json(block)
            await self.graph_db.insert(
                subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_USE_CASE, object_=detail.model_dump_json()
            )

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _rebuild_sequence_view(self, ns_class_name: str):
        """
        Asynchronously reconstructs the sequence diagram for the provided namespace-prefixed class name.

        Args:
            ns_class_name (str): The namespace-prefixed class name for which the sequence diagram is to be reconstructed.
        """
        await self._rebuild_use_case(ns_class_name)

        prompts_blocks = []
        use_case_markdown = await self._get_class_use_cases(ns_class_name)
        if not use_case_markdown:  # external class
            await self.graph_db.insert(subject=ns_class_name, predicate=GraphKeyword.HAS_SEQUENCE_VIEW, object_="")
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
            stream=False,
        )

        sequence_view = rsp.removeprefix("```mermaid").removesuffix("```")
        await self.graph_db.insert(
            subject=ns_class_name, predicate=GraphKeyword.HAS_SEQUENCE_VIEW, object_=sequence_view
        )

    async def _get_participants(self, ns_class_name: str) -> List[str]:
        """
        Asynchronously returns the participants list of the sequence diagram for the provided namespace-prefixed SPO
        object.

        Args:
            ns_class_name (str): The namespace-prefixed class name for which to retrieve the participants list.

        Returns:
            List[str]: A list of participants in the sequence diagram.
        """
        participants = set()
        detail = await self._get_class_detail(ns_class_name)
        if not detail:
            return []
        participants.update(set(detail.compositions))
        participants.update(set(detail.aggregations))
        return list(participants)

    async def _get_class_use_cases(self, ns_class_name: str) -> str:
        """
        Asynchronously assembles the context about the use case information of the namespace-prefixed SPO object.

        Args:
            ns_class_name (str): The namespace-prefixed class name for which to retrieve use case information.

        Returns:
            str: A string containing the assembled context about the use case information.
        """
        block = ""
        rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_USE_CASE)
        for i, r in enumerate(rows):
            detail = ReverseUseCaseDetails.model_validate_json(r.object_)
            block += f"\n### {i + 1}. {detail.description}"
            for j, use_case in enumerate(detail.use_cases):
                block += f"\n#### {i + 1}.{j + 1}. {use_case.description}\n"
                block += "\n##### Inputs\n" + "\n".join([f"- {s}" for s in use_case.inputs])
                block += "\n##### Outputs\n" + "\n".join([f"- {s}" for s in use_case.outputs])
                block += "\n##### Actors\n" + "\n".join([f"- {s}" for s in use_case.actors])
                block += "\n##### Steps\n" + "\n".join([f"- {s}" for s in use_case.steps])
            block += "\n#### Use Case Relationship\n" + "\n".join([f"- {s}" for s in detail.relationship])
        return block + "\n"

    async def _get_class_detail(self, ns_class_name: str) -> DotClassInfo | None:
        """
        Asynchronously retrieves the dot format class details of the namespace-prefixed SPO object.

        Args:
            ns_class_name (str): The namespace-prefixed class name for which to retrieve class details.

        Returns:
            Union[DotClassInfo, None]: A DotClassInfo object representing the dot format class details,
                                       or None if the details are not available.
        """
        rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_DETAIL)
        if not rows:
            return None
        dot_class_info = DotClassInfo.model_validate_json(rows[0].object_)
        return dot_class_info

    async def _get_uml_class_view(self, ns_class_name: str) -> UMLClassView | None:
        """
        Asynchronously retrieves the UML 2.0 format class details of the namespace-prefixed SPO object.

        Args:
            ns_class_name (str): The namespace-prefixed class name for which to retrieve UML class details.

        Returns:
            Union[UMLClassView, None]: A UMLClassView object representing the UML 2.0 format class details,
                                       or None if the details are not available.
        """
        rows = await self.graph_db.select(subject=ns_class_name, predicate=GraphKeyword.HAS_CLASS_VIEW)
        if not rows:
            return None
        class_view = UMLClassView.model_validate_json(rows[0].object_)
        return class_view

    async def _get_source_code(self, ns_class_name: str) -> str:
        """
        Asynchronously retrieves the source code of the namespace-prefixed SPO object.

        Args:
            ns_class_name (str): The namespace-prefixed class name for which to retrieve the source code.

        Returns:
            str: A string containing the source code of the specified namespace-prefixed class.
        """
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
        """
        Convert package name to the full path of the module.

        Args:
            root (Union[str, Path]): The root path or string representing the package.
            pathname (Union[str, Path]): The pathname or string representing the module.

        Returns:
            Union[Path, None]: The full path of the module, or None if the path cannot be determined.

        Examples:
            If `root`(workdir) is "/User/xxx/github/MetaGPT/metagpt", and the `pathname` is
            "metagpt/management/skill_manager.py", then the returned value will be
            "/User/xxx/github/MetaGPT/metagpt/management/skill_manager.py"
        """
        if re.match(r"^/.+", pathname):
            return pathname
        files = list_files(root=root)
        postfix = "/" + str(pathname)
        for i in files:
            if str(i).endswith(postfix):
                return i
        return None

    @staticmethod
    def parse_participant(mermaid_sequence_diagram: str) -> List[str]:
        """
        Parses the provided Mermaid sequence diagram and returns the list of participants.

        Args:
            mermaid_sequence_diagram (str): The Mermaid sequence diagram string to be parsed.

        Returns:
            List[str]: A list of participants extracted from the sequence diagram.
        """
        pattern = r"participant ([\w\.]+)"
        matches = re.findall(pattern, mermaid_sequence_diagram)
        matches = [re.sub(r"[\\/'\"]+", "", i) for i in matches]
        return matches

    async def _search_new_participant(self, entry: SPO) -> str | None:
        """
        Asynchronously retrieves a participant whose sequence diagram has not been augmented.

        Args:
            entry (SPO): The SPO object representing the relationship in the graph database.

        Returns:
            Union[str, None]: A participant whose sequence diagram has not been augmented, or None if not found.
        """
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
        """
        Augments the sequence diagram of `class_name` to the sequence diagram of `entry`.

        Args:
            entry (SPO): The SPO object representing the base sequence diagram.
            class_name (str): The class name whose sequence diagram is to be augmented.
        """
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
            return
        if len(participants) > 1:
            for r in participants:
                await self.graph_db.insert(
                    subject=entry.subject, predicate=GraphKeyword.HAS_PARTICIPANT, object_=auto_namespace(r.subject)
                )
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
            stream=False,
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
        await self._save_sequence_view(subject=entry.subject, content=sequence_view)

    async def _save_sequence_view(self, subject: str, content: str):
        pattern = re.compile(r"[^a-zA-Z0-9]")
        name = re.sub(pattern, "_", subject)
        filename = Path(name).with_suffix(".sequence_diagram.mmd")
        await self.context.repo.resources.data_api_design.save(filename=str(filename), content=content)

    async def _search_participants(self, filename: str) -> Set:
        content = await self._get_source_code(filename)

        rsp = await self.llm.aask(
            msg=content,
            system_msgs=[
                "You are a tool for listing all class names used in a source file.",
                "Return a markdown JSON object with: "
                '- a "class_names" key containing the list of class names used in the file; '
                '- a "reasons" key lists all reason objects, each object containing a "class_name" key for class name, a "reference" key explaining the line where the class has been used.',
            ],
        )

        class _Data(BaseModel):
            class_names: List[str]
            reasons: List

        json_blocks = parse_json_code_block(rsp)
        data = _Data.model_validate_json(json_blocks[0])
        return set(data.class_names)
