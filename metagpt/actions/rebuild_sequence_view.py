#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/4
# @Author  : mashenquan
# @File    : rebuild_sequence_view.py
# @Desc    : Rebuild sequence view info

from __future__ import annotations

from pathlib import Path
from typing import List

from metagpt.actions import Action
from metagpt.config2 import config
from metagpt.const import GRAPH_REPO_FILE_REPO
from metagpt.logs import logger
from metagpt.utils.common import aread, list_files
from metagpt.utils.di_graph_repository import DiGraphRepository
from metagpt.utils.graph_repository import GraphKeyword


class RebuildSequenceView(Action):
    """Class to rebuild sequence views for graph entries.

    This class is responsible for rebuilding the sequence views of graph entries
    by translating Python code into Mermaid Sequence Diagrams.

    Attributes:
        context: The context containing the git repository information.
        i_context: The input context for file operations.
        llm: The language model used for translation.
    """

    async def run(self, with_messages=None, format=config.prompt_schema):
        """Runs the action to rebuild sequence views for all main entries in the graph database.

        Args:
            with_messages: Optional; messages to display during the run.
            format: The format of the prompt schema, defaults to the configuration's prompt schema.
        """
        graph_repo_pathname = self.context.git_repo.workdir / GRAPH_REPO_FILE_REPO / self.context.git_repo.workdir.name
        graph_db = await DiGraphRepository.load_from(str(graph_repo_pathname.with_suffix(".json")))
        entries = await RebuildSequenceView._search_main_entry(graph_db)
        for entry in entries:
            await self._rebuild_sequence_view(entry, graph_db)
        await graph_db.save()

    @staticmethod
    async def _search_main_entry(graph_db) -> List:
        """Searches for main entries in the graph database.

        Main entries are identified by having a page info predicate and containing the tag '__name__:__main__'.

        Args:
            graph_db: The graph database to search within.

        Returns:
            A list of entries considered as main entries.
        """
        rows = await graph_db.select(predicate=GraphKeyword.HAS_PAGE_INFO)
        tag = "__name__:__main__"
        entries = []
        for r in rows:
            if tag in r.subject or tag in r.object_:
                entries.append(r)
        return entries

    async def _rebuild_sequence_view(self, entry, graph_db):
        """Rebuilds the sequence view for a given entry.

        Translates the Python code associated with the entry into a Mermaid Sequence Diagram.

        Args:
            entry: The entry for which to rebuild the sequence view.
            graph_db: The graph database where the entry is stored.
        """
        filename = entry.subject.split(":", 1)[0]
        src_filename = RebuildSequenceView._get_full_filename(root=self.i_context, pathname=filename)
        if not src_filename:
            return
        content = await aread(filename=src_filename, encoding="utf-8")
        content = f"```python\n{content}\n```\n\n---\nTranslate the code above into Mermaid Sequence Diagram."
        data = await self.llm.aask(
            msg=content, system_msgs=["You are a python code to Mermaid Sequence Diagram translator in function detail"]
        )
        await graph_db.insert(subject=filename, predicate=GraphKeyword.HAS_SEQUENCE_VIEW, object_=data)
        logger.info(data)

    @staticmethod
    def _get_full_filename(root: str | Path, pathname: str | Path) -> Path | None:
        """Finds the full filename for a given pathname within the root directory.

        Args:
            root: The root directory to search within.
            pathname: The pathname of the file to find.

        Returns:
            The full path to the file if found, None otherwise.
        """
        files = list_files(root=root)
        postfix = "/" + str(pathname)
        for i in files:
            if str(i).endswith(postfix):
                return i
        return None
