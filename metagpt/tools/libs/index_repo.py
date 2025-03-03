#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import tiktoken
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import NodeWithScore
from pydantic import BaseModel, Field, model_validator

from metagpt.config2 import config
from metagpt.context import Context
from metagpt.logs import logger
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.factories.embedding import RAGEmbeddingFactory
from metagpt.rag.schema import FAISSIndexConfig, FAISSRetrieverConfig, LLMRankerConfig
from metagpt.utils.common import aread, awrite, generate_fingerprint, list_files
from metagpt.utils.file import File
from metagpt.utils.report import EditorReporter

UPLOADS_INDEX_ROOT = "/data/.index/uploads"
DEFAULT_INDEX_ROOT = UPLOADS_INDEX_ROOT
UPLOAD_ROOT = "/data/uploads"
DEFAULT_ROOT = UPLOAD_ROOT
CHATS_INDEX_ROOT = "/data/.index/chats"
CHATS_ROOT = "/data/chats/"
OTHER_TYPE = "other"

DEFAULT_MIN_TOKEN_COUNT = 10000
DEFAULT_MAX_TOKEN_COUNT = 100000000


class IndexRepoMeta(BaseModel):
    min_token_count: int
    max_token_count: int


class TextScore(BaseModel):
    filename: str
    text: str
    score: Optional[float] = None


class IndexRepo(BaseModel):
    persist_path: str = DEFAULT_INDEX_ROOT  # The persist path of the index repo, `/data/.index/uploads/` or `/data/.index/chats/{chat_id}/`
    root_path: str = (
        DEFAULT_ROOT  # `/data/uploads` or r`/data/chats/[a-z0-9]+`, the root path of files indexed by the index repo.
    )
    fingerprint_filename: str = "fingerprint.json"
    meta_filename: str = "meta.json"
    model: Optional[str] = None
    min_token_count: int = DEFAULT_MIN_TOKEN_COUNT
    max_token_count: int = DEFAULT_MAX_TOKEN_COUNT
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
        filenames, excludes = await self._filter(filenames)
        if not filenames:
            raise ValueError(f"Unsupported file types: {[str(i) for i in excludes]}")
        resource = EditorReporter()
        for i in filenames:
            await resource.async_report(str(i), "path")
        filter_filenames = set()
        meta = await self._read_meta()
        new_files = {}
        for i in filenames:
            if Path(i).suffix.lower() in {".pdf", ".doc", ".docx"}:
                if str(i) not in self.fingerprints:
                    new_files[i] = ""
                    logger.warning(f'file: "{i}" not indexed')
                filter_filenames.add(str(i))
                continue
            content = await File.read_text_file(i)
            token_count = len(encoding.encode(content))
            if not self._is_buildable(
                token_count, min_token_count=meta.min_token_count, max_token_count=meta.max_token_count
            ):
                result.append(TextScore(filename=str(i), text=content))
                continue
            file_fingerprint = generate_fingerprint(content)
            if str(i) not in self.fingerprints or (self.fingerprints.get(str(i)) != file_fingerprint):
                new_files[i] = content
                logger.warning(f'file: "{i}" changed but not indexed')
                continue
            filter_filenames.add(str(i))
        if new_files:
            added, others = await self.add(paths=list(new_files.keys()), file_datas=new_files)
            filter_filenames.update([str(i) for i in added])
            for i in others:
                result.append(TextScore(filename=str(i), text=new_files.get(i)))
                filter_filenames.discard(str(i))
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
        flat_nodes = [node for indices in indices_list if indices for node in indices if node]
        if len(flat_nodes) <= self.recall_count:
            return flat_nodes

        if not self.embedding:
            if self.model:
                config.embedding.model = self.model
            factory = RAGEmbeddingFactory(config)
            self.embedding = factory.get_rag_embedding()

        scores = []
        query_embedding = await self.embedding.aget_text_embedding(query)
        for i in flat_nodes:
            try:
                text_embedding = await self.embedding.aget_text_embedding(i.text)
            except Exception as e:  # 超过最大长度
                tenth = int(len(i.text) / 10)  # DEFAULT_MIN_TOKEN_COUNT = 10000
                logger.warning(
                    f"{e}, tenth len={tenth}, pre_part_len={len(i.text[: tenth * 6])}, post_part_len={len(i.text[tenth * 4:])}"
                )
                pre_win_part = await self.embedding.aget_text_embedding(i.text[: tenth * 6])
                post_win_part = await self.embedding.aget_text_embedding(i.text[tenth * 4 :])
                similarity = max(
                    self.embedding.similarity(query_embedding, pre_win_part),
                    self.embedding.similarity(query_embedding, post_win_part),
                )
                scores.append((similarity, i))
                continue
            similarity = self.embedding.similarity(query_embedding, text_embedding)
            scores.append((similarity, i))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [i[1] for i in scores][: self.recall_count]

    async def add(
        self, paths: List[Path], file_datas: Dict[Union[str, Path], str] = None
    ) -> Tuple[List[str], List[str]]:
        """Add new documents to the index.

        Args:
            paths (List[Path]): A list of paths to the documents to be added.
            file_datas (Dict[Union[str, Path], str]): A list of file content.

        Returns:
        Tuple[List[str], List[str]]: A tuple containing two lists:
            1. The list of filenames that were successfully added to the index.
            2. The list of filenames that were not added to the index because they were not buildable.
        """
        encoding = tiktoken.get_encoding("cl100k_base")
        filenames, _ = await self._filter(paths)
        filter_filenames = []
        delete_filenames = []
        file_datas = file_datas or {}
        for i in filenames:
            content = file_datas.get(i) or await File.read_text_file(i)
            file_datas[i] = content
            if not self._is_fingerprint_changed(filename=i, content=content):
                continue
            token_count = len(encoding.encode(content))
            if self._is_buildable(token_count):
                filter_filenames.append(i)
                logger.debug(f"{i} is_buildable: {token_count}, {self.min_token_count}~{self.max_token_count}")
            else:
                delete_filenames.append(i)
                logger.debug(f"{i} not is_buildable: {token_count}, {self.min_token_count}~{self.max_token_count}")
        await self._add_batch(filenames=filter_filenames, delete_filenames=delete_filenames, file_datas=file_datas)
        return filter_filenames, delete_filenames

    async def _add_batch(
        self,
        filenames: List[Union[str, Path]],
        delete_filenames: List[Union[str, Path]],
        file_datas: Dict[Union[str, Path], str],
    ):
        """Add and remove documents in a batch operation.

        Args:
            filenames (List[Union[str, Path]]): List of filenames to add.
            delete_filenames (List[Union[str, Path]]): List of filenames to delete.
        """
        if not filenames:
            return
        logger.info(f"update index repo, add {filenames}, remove {delete_filenames}")
        engine = None
        Context()
        if Path(self.persist_path).exists():
            logger.debug(f"load index from {self.persist_path}")
            engine = SimpleEngine.from_index(
                index_config=FAISSIndexConfig(persist_path=self.persist_path),
                retriever_configs=[FAISSRetrieverConfig()],
            )
            try:
                engine.delete_docs(filenames + delete_filenames)
                logger.info(f"delete docs {filenames + delete_filenames}")
                engine.add_docs(input_files=filenames)
                logger.info(f"add docs {filenames}")
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
            logger.info(f"add docs {filenames}")
        engine.persist(persist_dir=self.persist_path)
        for i in filenames:
            content = file_datas.get(i) or await File.read_text_file(i)
            fp = generate_fingerprint(content)
            self.fingerprints[str(i)] = fp
        await awrite(filename=Path(self.persist_path) / self.fingerprint_filename, data=json.dumps(self.fingerprints))
        await self._save_meta()

    def __str__(self):
        """Return a string representation of the IndexRepo.

        Returns:
            str: The filename of the index repository.
        """
        return f"{self.persist_path}"

    def _is_buildable(self, token_count: int, min_token_count: int = -1, max_token_count=-1) -> bool:
        """Check if the token count is within the buildable range.

        Args:
            token_count (int): The number of tokens in the content.

        Returns:
            bool: True if buildable, False otherwise.
        """
        min_token_count = min_token_count if min_token_count >= 0 else self.min_token_count
        max_token_count = max_token_count if max_token_count >= 0 else self.max_token_count
        if token_count < min_token_count or token_count > max_token_count:
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
                is_text = await File.is_textual_file(path)
                if is_text:
                    pathnames.append(path)
                continue
            subfiles = list_files(path)
            for j in subfiles:
                is_text = await File.is_textual_file(j)
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
        if not filters:
            return []
        if not Path(self.persist_path).exists():
            raise ValueError(f"IndexRepo {Path(self.persist_path).name} not exists.")
        Context()
        engine = SimpleEngine.from_index(
            index_config=FAISSIndexConfig(persist_path=self.persist_path),
            retriever_configs=[FAISSRetrieverConfig()],
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

    @staticmethod
    def find_index_repo_path(files: List[Union[str, Path]]) -> Tuple[Dict[str, Set[Path]], Dict[str, str]]:
        """Map the file path to the corresponding index repo.

        Args:
            files (List[Union[str, Path]]): A list of file paths or Path objects to be classified.

        Returns:
            Tuple[Dict[str, Set[Path]], Dict[str, str]]:
                - A dictionary mapping the index repo path to the files.
                - A dictionary mapping the index repo path to their corresponding root directories.
        """
        mappings = {
            UPLOADS_INDEX_ROOT: re.compile(r"^/data/uploads($|/.*)"),
            CHATS_INDEX_ROOT: re.compile(r"^/data/chats/[a-z0-9]+($|/.*)"),
        }

        clusters = {}
        roots = {}
        for i in files:
            path = Path(i).absolute()
            path_type = OTHER_TYPE
            for type_, pattern in mappings.items():
                if re.match(pattern, str(i)):
                    path_type = type_
                    break
            if path_type == CHATS_INDEX_ROOT:
                chat_id = path.parts[3]
                path_type = str(Path(path_type) / chat_id)
                roots[path_type] = str(Path(CHATS_ROOT) / chat_id)
            elif path_type == UPLOADS_INDEX_ROOT:
                roots[path_type] = UPLOAD_ROOT

            if path_type in clusters:
                clusters[path_type].add(path)
            else:
                clusters[path_type] = {path}

        return clusters, roots

    async def _save_meta(self):
        meta = IndexRepoMeta(min_token_count=self.min_token_count, max_token_count=self.max_token_count)
        await awrite(filename=Path(self.persist_path) / self.meta_filename, data=meta.model_dump_json())

    async def _read_meta(self) -> IndexRepoMeta:
        default_meta = IndexRepoMeta(min_token_count=self.min_token_count, max_token_count=self.max_token_count)

        filename = Path(self.persist_path) / self.meta_filename
        if not filename.exists():
            return default_meta
        meta_data = await aread(filename=filename)
        try:
            meta = IndexRepoMeta.model_validate_json(meta_data)
            return meta
        except Exception as e:
            logger.warning(f"Load meta error: {e}")
        return default_meta

    @staticmethod
    async def cross_repo_search(query: str, file_or_path: Union[str, Path]) -> List[str]:
        """Search for a query across multiple repositories.

        This asynchronous function searches for the specified query in files
        located at the given path or file.

        Args:
            query (str): The search term to look for in the files.
            file_or_path (Union[str, Path]): The path to the file or directory
                where the search should be conducted. This can be a string path
                or a Path object.

        Returns:
            List[str]: A list of strings containing the paths of files that
            contain the query results.

        Raises:
            ValueError: If the query string is empty.
        """
        if not file_or_path or not Path(file_or_path).exists():
            raise ValueError(f'"{str(file_or_path)}" not exists')
        files = [file_or_path] if not Path(file_or_path).is_dir() else list_files(file_or_path)
        clusters, roots = IndexRepo.find_index_repo_path(files)
        futures = []
        others = set()
        for persist_path, filenames in clusters.items():
            if persist_path == OTHER_TYPE:
                others.update(filenames)
                continue
            root = roots[persist_path]
            repo = IndexRepo(persist_path=persist_path, root_path=root)
            futures.append(repo.search(query=query, filenames=list(filenames)))

        for i in others:
            futures.append(File.read_text_file(i))

        futures_results = []
        if futures:
            futures_results = await asyncio.gather(*futures)

        result = []
        v_result = []
        for i in futures_results:
            if not i:
                continue
            if isinstance(i, str):
                result.append(i)
            else:
                v_result.append(i)

        repo = IndexRepo()
        merged = await repo.merge(query=query, indices_list=v_result)
        return [i.text for i in merged] + result
