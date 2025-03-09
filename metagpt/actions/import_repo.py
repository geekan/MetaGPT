#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

This script defines an action to import a Git repository into the MetaGPT project format, enabling incremental
 appending of requirements.
The MetaGPT project format encompasses a structured representation of project data compatible with MetaGPT's
 capabilities, facilitating the integration of Git repositories into MetaGPT workflows while allowing for the gradual
 addition of requirements.

"""
import json
import re
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

from metagpt.actions import Action
from metagpt.actions.extract_readme import ExtractReadMe
from metagpt.actions.rebuild_class_view import RebuildClassView
from metagpt.actions.rebuild_sequence_view import RebuildSequenceView
from metagpt.const import GRAPH_REPO_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.tools.libs.git import git_clone
from metagpt.utils.common import (
    aread,
    awrite,
    list_files,
    parse_json_code_block,
    split_namespace,
)
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.git_repository import GitRepository
from metagpt.utils.graph_repository import GraphKeyword, GraphRepository
from metagpt.utils.project_repo import ProjectRepo


class ImportRepo(Action):
    """
    An action to import a Git repository into a graph database and create related artifacts.

    Attributes:
        repo_path (str): The URL of the Git repository to import.
        graph_db (Optional[GraphRepository]): The output graph database of the Git repository.
        rid (str): The output requirement ID.
    """

    repo_path: str  # input, git repo url.
    graph_db: Optional[GraphRepository] = None  # output. graph db of the git repository
    rid: str = ""  # output, requirement ID.

    async def run(self, with_messages: List[Message] = None, **kwargs) -> Message:
        """
        Runs the import process for the Git repository.

        Args:
            with_messages (List[Message], optional): Additional messages to include.
            **kwargs: Additional keyword arguments.

        Returns:
            Message: A message indicating the completion of the import process.
        """
        await self._create_repo()
        await self._create_prd()
        await self._create_system_design()
        self.context.git_repo.archive(comments="Import")

    async def _create_repo(self):
        path = await git_clone(url=self.repo_path, output_dir=self.config.workspace.path)
        self.repo_path = str(path)
        self.config.project_path = path
        self.context.git_repo = GitRepository(local_path=path, auto_init=True)
        self.context.repo = ProjectRepo(self.context.git_repo)
        self.context.src_workspace = await self._guess_src_workspace()
        await awrite(
            filename=self.context.repo.workdir / ".src_workspace",
            data=str(self.context.src_workspace.relative_to(self.context.repo.workdir)),
        )

    async def _create_prd(self):
        action = ExtractReadMe(i_context=str(self.context.repo.workdir), context=self.context)
        await action.run()
        graph_repo_pathname = self.context.git_repo.workdir / GRAPH_REPO_FILE_REPO / self.context.git_repo.workdir.name
        self.graph_db = await DiGraphRepository.load_from(str(graph_repo_pathname.with_suffix(".json")))
        rows = await self.graph_db.select(predicate=GraphKeyword.HAS_SUMMARY)
        prd = {"Project Name": self.context.repo.workdir.name}
        for r in rows:
            if Path(r.subject).stem == "README":
                prd["Original Requirements"] = r.object_
                break
        self.rid = FileRepository.new_filename()
        await self.repo.docs.prd.save(filename=self.rid + ".json", content=json.dumps(prd))

    async def _create_system_design(self):
        action = RebuildClassView(
            name="ReverseEngineering", i_context=str(self.context.src_workspace), context=self.context
        )
        await action.run()
        rows = await action.graph_db.select(predicate="hasMermaidClassDiagramFile")
        class_view_filename = rows[0].object_
        logger.info(f"class view:{class_view_filename}")

        rows = await action.graph_db.select(predicate=GraphKeyword.HAS_PAGE_INFO)
        tag = "__name__:__main__"
        entries = []
        src_workspace = self.context.src_workspace.relative_to(self.context.repo.workdir)
        for r in rows:
            if tag in r.subject:
                path = split_namespace(r.subject)[0]
            elif tag in r.object_:
                path = split_namespace(r.object_)[0]
            else:
                continue
            if Path(path).is_relative_to(src_workspace):
                entries.append(Path(path))
        main_entry = await self._guess_main_entry(entries)
        full_path = RebuildSequenceView.get_full_filename(self.context.repo.workdir, main_entry)
        action = RebuildSequenceView(context=self.context, i_context=str(full_path))
        try:
            await action.run()
        except Exception as e:
            logger.warning(f"{e}, use the last successful version.")
        files = list_files(self.context.repo.resources.data_api_design.workdir)
        pattern = re.compile(r"[^a-zA-Z0-9]")
        name = re.sub(pattern, "_", str(main_entry))
        filename = Path(name).with_suffix(".sequence_diagram.mmd")
        postfix = str(filename)
        sequence_files = [i for i in files if postfix in str(i)]
        content = await aread(filename=sequence_files[0])
        await self.context.repo.resources.data_api_design.save(
            filename=self.repo.workdir.stem + ".sequence_diagram.mmd", content=content
        )
        await self._save_system_design()

    async def _save_system_design(self):
        class_view = await self.context.repo.resources.data_api_design.get(
            filename=self.repo.workdir.stem + ".class_diagram.mmd"
        )
        sequence_view = await self.context.repo.resources.data_api_design.get(
            filename=self.repo.workdir.stem + ".sequence_diagram.mmd"
        )
        file_list = self.context.git_repo.get_files(relative_path=".", root_relative_path=self.context.src_workspace)
        data = {
            "Data structures and interfaces": class_view.content,
            "Program call flow": sequence_view.content,
            "File list": [str(i) for i in file_list],
        }
        await self.context.repo.docs.system_design.save(filename=self.rid + ".json", content=json.dumps(data))

    async def _guess_src_workspace(self) -> Path:
        files = list_files(self.context.repo.workdir)
        dirs = [i.parent for i in files if i.name == "__init__.py"]
        distinct = set()
        for i in dirs:
            done = False
            for j in distinct:
                if i.is_relative_to(j):
                    done = True
                    break
                if j.is_relative_to(i):
                    break
            if not done:
                distinct = {j for j in distinct if not j.is_relative_to(i)}
                distinct.add(i)
        if len(distinct) == 1:
            return list(distinct)[0]
        prompt = "\n".join([f"- {str(i)}" for i in distinct])
        rsp = await self.llm.aask(
            prompt,
            system_msgs=[
                "You are a tool to choose the source code path from a list of paths based on the directory name.",
                "You should identify the source code path among paths such as unit test path, examples path, etc.",
                "Return a markdown JSON object containing:\n"
                '- a "src" field containing the source code path;\n'
                '- a "reason" field containing explaining why other paths is not the source code path\n',
            ],
        )
        logger.debug(rsp)
        json_blocks = parse_json_code_block(rsp)

        class Data(BaseModel):
            src: str
            reason: str

        data = Data.model_validate_json(json_blocks[0])
        logger.info(f"src_workspace: {data.src}")
        return Path(data.src)

    async def _guess_main_entry(self, entries: List[Path]) -> Path:
        if len(entries) == 1:
            return entries[0]

        file_list = "## File List\n"
        file_list += "\n".join([f"- {i}" for i in entries])

        rows = await self.graph_db.select(predicate=GraphKeyword.HAS_USAGE)
        usage = "## Usage\n"
        for r in rows:
            if Path(r.subject).stem == "README":
                usage += r.object_

        prompt = file_list + "\n---\n" + usage
        rsp = await self.llm.aask(
            prompt,
            system_msgs=[
                'You are a tool to choose the source file path from "File List" which is used in "Usage".',
                'You choose the source file path based on the name of file and the class name and package name used in "Usage".',
                "Return a markdown JSON object containing:\n"
                '- a "filename" field containing the chosen source file path from "File List" which is used in "Usage";\n'
                '- a "reason" field explaining why.',
            ],
            stream=False,
        )
        logger.debug(rsp)
        json_blocks = parse_json_code_block(rsp)

        class Data(BaseModel):
            filename: str
            reason: str

        data = Data.model_validate_json(json_blocks[0])
        logger.info(f"main: {data.filename}")
        return Path(data.filename)
