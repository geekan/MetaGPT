#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

import tiktoken
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import NodeWithScore
from pydantic import BaseModel, Field, model_validator

from metagpt.config2 import Config
from metagpt.logs import logger
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.factories.embedding import RAGEmbeddingFactory
from metagpt.rag.schema import FAISSIndexConfig, FAISSRetrieverConfig, LLMRankerConfig
from metagpt.utils.common import aread, awrite, generate_fingerprint, list_files
from metagpt.utils.repo_to_markdown import is_text_file


class TextScore(BaseModel):
    filename: str
    text: str
    score: Optional[float] = None


class IndexRepo(BaseModel):
    persist_path: str  # The persist path of the index repo, {DEFAULT_WORKSPACE_ROOT}/.index/{chat_id or 'uploads'}/
    root_path: str  # `/data/uploads` or r`/data/chats/\d+`, the root path of files indexed by the index repo.
    fingerprint_filename: str = "fingerprint.json"
    model: Optional[str] = None
    min_token_count: int = 10000
    max_token_count: int = 100000000
    recall_count: int = 5
    embedding: Optional[BaseEmbedding] = Field(default=None, exclude=True)
    fingerprints: Dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _update_fingerprints(self) -> "IndexRepo":
        """Load fingerprints from the fingerprint file if not already loaded.

        Returns:
            IndexRepo: The updated IndexRepo instance.
        """
        if not self.fingerprints:
            filename = Path(self.persist_path) / self.fingerprint_filename
            if not filename.exists():
                return self
            with open(str(filename), "r") as reader:
                self.fingerprints = json.load(reader)
        return self

    async def search(
        self, query: str, filenames: Optional[List[Path]] = None
    ) -> Optional[List[Union[NodeWithScore, TextScore]]]:
        """Search for documents related to the given query.

        Args:
            query (str): The search query.
            filenames (Optional[List[Path]]): A list of filenames to filter the search.

        Returns:
            Optional[List[Union[NodeWithScore, TextScore]]]: A list of search results containing NodeWithScore or TextScore.
        """
        encoding = tiktoken.get_encoding("cl100k_base")
        result: List[Union[NodeWithScore, TextScore]] = []
        filenames, _ = await self._filter(filenames)
        filter_filenames = set()
        for i in filenames:
            content = await aread(filename=i)
            token_count = len(encoding.encode(content))
            if not self._is_buildable(token_count):
                result.append(TextScore(filename=str(i), text=content))
                continue
            file_fingerprint = generate_fingerprint(content)
            if self.fingerprints.get(str(i)) != file_fingerprint:
                logger.error(f'file: "{i}" changed but not indexed')
                continue
            filter_filenames.add(str(i))
        nodes = await self._search(query=query, filters=filter_filenames)
        return result + nodes

    async def merge(
        self, query: str, indices_list: List[List[Union[NodeWithScore, TextScore]]]
    ) -> List[Union[NodeWithScore, TextScore]]:
        """Merge results from multiple indices based on the query.

        Args:
            query (str): The search query.
            indices_list (List[List[Union[NodeWithScore, TextScore]]]): A list of result lists from different indices.

        Returns:
            List[Union[NodeWithScore, TextScore]]: A list of merged results sorted by similarity.
        """
        if not self.embedding:
            config = Config.default()
            if self.model:
                config.embedding.model = self.model
            factory = RAGEmbeddingFactory(config)
            self.embedding = factory.get_rag_embedding()

        scores = []
        query_embedding = await self.embedding.aget_text_embedding(query)
        flat_nodes = [node for indices in indices_list for node in indices]
        for i in flat_nodes:
            text_embedding = await self.embedding.aget_text_embedding(i.text)
            similarity = self.embedding.similarity(query_embedding, text_embedding)
            scores.append((similarity, i))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [i[1] for i in scores][: self.recall_count]

    async def add(self, paths: List[Path]):
        """Add new documents to the index.

        Args:
            paths (List[Path]): A list of paths to the documents to be added.
        """
        encoding = tiktoken.get_encoding("cl100k_base")
        filenames, _ = await self._filter(paths)
        filter_filenames = []
        delete_filenames = []
        for i in filenames:
            content = await aread(filename=i)
            if not self._is_fingerprint_changed(filename=i, content=content):
                continue
            token_count = len(encoding.encode(content))
            if self._is_buildable(token_count):
                filter_filenames.append(i)
                logger.debug(f"{i} is_buildable: {token_count}, {self.min_token_count}~{self.max_token_count}")
            else:
                delete_filenames.append(i)
                logger.debug(f"{i} not is_buildable: {token_count}, {self.min_token_count}~{self.max_token_count}")
        await self._add_batch(filenames=filter_filenames, delete_filenames=delete_filenames)

    async def _add_batch(self, filenames: List[Union[str, Path]], delete_filenames: List[Union[str, Path]]):
        """Add and remove documents in a batch operation.

        Args:
            filenames (List[Union[str, Path]]): List of filenames to add.
            delete_filenames (List[Union[str, Path]]): List of filenames to delete.
        """
        if not filenames:
            return
        logger.info(f"update index repo, add {filenames}, remove {delete_filenames}")
        engine = None
        if Path(self.persist_path).exists():
            logger.debug(f"load index from {self.persist_path}")
            engine = SimpleEngine.from_index(
                index_config=FAISSIndexConfig(persist_path=self.persist_path),
                retriever_configs=[FAISSRetrieverConfig()],
            )
            try:
                engine.delete_docs(filenames + delete_filenames)
                logger.debug(f"delete docs {filenames + delete_filenames}")
                engine.add_docs(input_files=filenames)
                logger.debug(f"add docs {filenames}")
            except NotImplementedError as e:
                logger.debug(f"{e}")
                filenames = list(set([str(i) for i in filenames] + list(self.fingerprints.keys())))
                engine = None
                logger.info(f"{e}. Rebuild all.")
        if not engine:
            engine = SimpleEngine.from_docs(
                input_files=[str(i) for i in filenames],
                retriever_configs=[FAISSRetrieverConfig()],
                ranker_configs=[LLMRankerConfig()],
            )
            logger.debug(f"add docs {filenames}")
        engine.persist(persist_dir=self.persist_path)
        for i in filenames:
            content = await aread(i)
            fp = generate_fingerprint(content)
            self.fingerprints[str(i)] = fp
        await awrite(filename=Path(self.persist_path) / self.fingerprint_filename, data=json.dumps(self.fingerprints))

    def __str__(self):
        """Return a string representation of the IndexRepo.

        Returns:
            str: The filename of the index repository.
        """
        return f"{self.persist_path}"

    def _is_buildable(self, token_count: int) -> bool:
        """Check if the token count is within the buildable range.

        Args:
            token_count (int): The number of tokens in the content.

        Returns:
            bool: True if buildable, False otherwise.
        """
        if token_count < self.min_token_count or token_count > self.max_token_count:
            return False
        return True

    async def _filter(self, filenames: Optional[List[Union[str, Path]]] = None) -> (List[Path], List[Path]):
        """Filter the provided filenames to only include valid text files.

        Args:
            filenames (Optional[List[Union[str, Path]]]): List of filenames to filter.

        Returns:
            Tuple[List[Path], List[Path]]: A tuple containing a list of valid pathnames and a list of excluded paths.
        """
        root_path = Path(self.root_path).absolute()
        if not filenames:
            filenames = [root_path]
        pathnames = []
        excludes = []
        for i in filenames:
            path = Path(i).absolute()
            if not path.is_relative_to(root_path):
                excludes.append(path)
                logger.debug(f"{path} not is_relative_to {root_path})")
                continue
            if not path.is_dir():
                is_text, _ = await is_text_file(path)
                if is_text:
                    pathnames.append(path)
                continue
            subfiles = list_files(path)
            for j in subfiles:
                is_text, _ = await is_text_file(j)
                if is_text:
                    pathnames.append(j)

        logger.debug(f"{pathnames}, excludes:{excludes})")
        return pathnames, excludes

    async def _search(self, query: str, filters: Set[str]) -> List[NodeWithScore]:
        """Perform a search for the given query using the index.

        Args:
            query (str): The search query.
            filters (Set[str]): A set of filenames to filter the search results.

        Returns:
            List[NodeWithScore]: A list of nodes with scores matching the query.
        """
        if not Path(self.persist_path).exists():
            return []
        engine = SimpleEngine.from_index(
            index_config=FAISSIndexConfig(persist_path=self.persist_path), retriever_configs=[FAISSRetrieverConfig()]
        )
        rsp = await engine.aretrieve(query)
        return [i for i in rsp if i.metadata.get("file_path") in filters]

    def _is_fingerprint_changed(self, filename: Union[str, Path], content: str) -> bool:
        """Check if the fingerprint of the given document content has changed.

        Args:
            filename (Union[str, Path]): The filename of the document.
            content (str): The content of the document.

        Returns:
            bool: True if the fingerprint has changed, False otherwise.
        """
        old_fp = self.fingerprints.get(str(filename))
        if not old_fp:
            return True
        fp = generate_fingerprint(content)
        return old_fp != fp
