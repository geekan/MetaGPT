"""Simple Engine."""

import json
import os
from typing import Any, Optional, Union

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.embeddings.mock_embed_model import MockEmbedding
from llama_index.core.indices.base import BaseIndex
from llama_index.core.ingestion.pipeline import run_transformations
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import (
    BaseSynthesizer,
    get_response_synthesizer,
)
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import (
    BaseNode,
    Document,
    NodeWithScore,
    QueryBundle,
    QueryType,
    TransformComponent,
)

from metagpt.rag.factories import (
    get_index,
    get_rag_embedding,
    get_rag_llm,
    get_rankers,
    get_retriever,
)
from metagpt.rag.interface import NoEmbedding, RAGObject
from metagpt.rag.retrievers.base import ModifiableRAGRetriever, PersistableRAGRetriever
from metagpt.rag.retrievers.hybrid_retriever import SimpleHybridRetriever
from metagpt.rag.schema import (
    BaseIndexConfig,
    BaseRankerConfig,
    BaseRetrieverConfig,
    BM25RetrieverConfig,
    ObjectNode,
)
from metagpt.utils.common import import_class


class SimpleEngine(RetrieverQueryEngine):
    """SimpleEngine is designed to be simple and straightforward.

    It is a lightweight and easy-to-use search engine that integrates
    document reading, embedding, indexing, retrieving, and ranking functionalities
    into a single, straightforward workflow. It is designed to quickly set up a
    search engine from a collection of documents.
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        response_synthesizer: Optional[BaseSynthesizer] = None,
        node_postprocessors: Optional[list[BaseNodePostprocessor]] = None,
        callback_manager: Optional[CallbackManager] = None,
        index: Optional[BaseIndex] = None,
    ) -> None:
        super().__init__(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=node_postprocessors,
            callback_manager=callback_manager,
        )
        self.index = index

    @classmethod
    def from_docs(
        cls,
        input_dir: str = None,
        input_files: list[str] = None,
        transformations: Optional[list[TransformComponent]] = None,
        embed_model: BaseEmbedding = None,
        llm: LLM = None,
        retriever_configs: list[BaseRetrieverConfig] = None,
        ranker_configs: list[BaseRankerConfig] = None,
    ) -> "SimpleEngine":
        """From docs.

        Must provide either `input_dir` or `input_files`.

        Args:
            input_dir: Path to the directory.
            input_files: List of file paths to read (Optional; overrides input_dir, exclude).
            transformations: Parse documents to nodes. Default [SentenceSplitter].
            embed_model: Parse nodes to embedding. Must supported by llama index. Default OpenAIEmbedding.
            llm: Must supported by llama index. Default OpenAI.
            retriever_configs: Configuration for retrievers. If more than one config, will use SimpleHybridRetriever.
            ranker_configs: Configuration for rankers.
        """
        if not input_dir and not input_files:
            raise ValueError("Must provide either `input_dir` or `input_files`.")

        documents = SimpleDirectoryReader(input_dir=input_dir, input_files=input_files).load_data()
        cls._fix_document_metadata(documents)

        index = VectorStoreIndex.from_documents(
            documents=documents,
            transformations=transformations or [SentenceSplitter()],
            embed_model=cls._resolve_embed_model(embed_model, retriever_configs),
        )
        return cls._from_index(index, llm=llm, retriever_configs=retriever_configs, ranker_configs=ranker_configs)

    @classmethod
    def from_objs(
        cls,
        objs: Optional[list[RAGObject]] = None,
        transformations: Optional[list[TransformComponent]] = None,
        embed_model: BaseEmbedding = None,
        llm: LLM = None,
        retriever_configs: list[BaseRetrieverConfig] = None,
        ranker_configs: list[BaseRankerConfig] = None,
    ) -> "SimpleEngine":
        """From objs.

        Args:
            objs: List of RAGObject.
            transformations: Parse documents to nodes. Default [SentenceSplitter].
            embed_model: Parse nodes to embedding. Must supported by llama index. Default OpenAIEmbedding.
            llm: Must supported by llama index. Default OpenAI.
            retriever_configs: Configuration for retrievers. If more than one config, will use SimpleHybridRetriever.
            ranker_configs: Configuration for rankers.
        """
        objs = objs or []
        retriever_configs = retriever_configs or []

        if not objs and any(isinstance(config, BM25RetrieverConfig) for config in retriever_configs):
            raise ValueError("In BM25RetrieverConfig, Objs must not be empty.")

        nodes = [ObjectNode(text=obj.rag_key(), metadata=ObjectNode.get_obj_metadata(obj)) for obj in objs]
        index = VectorStoreIndex(
            nodes=nodes,
            transformations=transformations or [SentenceSplitter()],
            embed_model=cls._resolve_embed_model(embed_model, retriever_configs),
        )
        return cls._from_index(index, llm=llm, retriever_configs=retriever_configs, ranker_configs=ranker_configs)

    @classmethod
    def from_index(
        cls,
        index_config: BaseIndexConfig,
        embed_model: BaseEmbedding = None,
        llm: LLM = None,
        retriever_configs: list[BaseRetrieverConfig] = None,
        ranker_configs: list[BaseRankerConfig] = None,
    ) -> "SimpleEngine":
        """Load from previously maintained index by self.persist(), index_config contains persis_path."""
        index = get_index(index_config, embed_model=cls._resolve_embed_model(embed_model, [index_config]))
        return cls._from_index(index, llm=llm, retriever_configs=retriever_configs, ranker_configs=ranker_configs)

    async def asearch(self, content: str, **kwargs) -> str:
        """Inplement tools.SearchInterface"""
        return await self.aquery(content)

    async def aretrieve(self, query: QueryType) -> list[NodeWithScore]:
        """Allow query to be str."""
        query_bundle = QueryBundle(query) if isinstance(query, str) else query

        nodes = await super().aretrieve(query_bundle)
        self._try_reconstruct_obj(nodes)
        return nodes

    def add_docs(self, input_files: list[str]):
        """Add docs to retriever. retriever must has add_nodes func."""
        self._ensure_retriever_modifiable()

        documents = SimpleDirectoryReader(input_files=input_files).load_data()
        self._fix_document_metadata(documents)

        nodes = run_transformations(documents, transformations=self.index._transformations)
        self._save_nodes(nodes)

    def add_objs(self, objs: list[RAGObject]):
        """Adds objects to the retriever, storing each object's original form in metadata for future reference."""
        self._ensure_retriever_modifiable()

        nodes = [ObjectNode(text=obj.rag_key(), metadata=ObjectNode.get_obj_metadata(obj)) for obj in objs]
        self._save_nodes(nodes)

    def persist(self, persist_dir: Union[str, os.PathLike], **kwargs):
        """Persist."""
        self._ensure_retriever_persistable()

        self._persist(str(persist_dir), **kwargs)

    @classmethod
    def _from_index(
        cls,
        index: BaseIndex,
        llm: LLM = None,
        retriever_configs: list[BaseRetrieverConfig] = None,
        ranker_configs: list[BaseRankerConfig] = None,
    ) -> "SimpleEngine":
        llm = llm or get_rag_llm()
        retriever = get_retriever(configs=retriever_configs, index=index)  # Default index.as_retriever
        rankers = get_rankers(configs=ranker_configs, llm=llm)  # Default []

        return cls(
            retriever=retriever,
            node_postprocessors=rankers,
            response_synthesizer=get_response_synthesizer(llm=llm),
            index=index,
        )

    def _ensure_retriever_modifiable(self):
        self._ensure_retriever_of_type(ModifiableRAGRetriever)

    def _ensure_retriever_persistable(self):
        self._ensure_retriever_of_type(PersistableRAGRetriever)

    def _ensure_retriever_of_type(self, required_type: BaseRetriever):
        """Ensure that self.retriever is required_type, or at least one of its components, if it's a SimpleHybridRetriever.

        Args:
            required_type: The class that the retriever is expected to be an instance of.
        """
        if isinstance(self.retriever, SimpleHybridRetriever):
            if not any(isinstance(r, required_type) for r in self.retriever.retrievers):
                raise TypeError(
                    f"Must have at least one retriever of type {required_type.__name__} in SimpleHybridRetriever"
                )

        if not isinstance(self.retriever, required_type):
            raise TypeError(f"The retriever is not of type {required_type.__name__}: {type(self.retriever)}")

    def _save_nodes(self, nodes: list[BaseNode]):
        self.retriever.add_nodes(nodes)

    def _persist(self, persist_dir: str, **kwargs):
        self.retriever.persist(persist_dir, **kwargs)

    @staticmethod
    def _try_reconstruct_obj(nodes: list[NodeWithScore]):
        """If node is object, then dynamically reconstruct object, and save object to node.metadata["obj"]."""
        for node in nodes:
            if node.metadata.get("is_obj", False):
                obj_cls = import_class(node.metadata["obj_cls_name"], node.metadata["obj_mod_name"])
                obj_dict = json.loads(node.metadata["obj_json"])
                node.metadata["obj"] = obj_cls(**obj_dict)

    @staticmethod
    def _fix_document_metadata(documents: list[Document]):
        """LlamaIndex keep metadata['file_path'], which is unnecessary, maybe deleted in the near future."""
        for doc in documents:
            doc.excluded_embed_metadata_keys.append("file_path")

    @staticmethod
    def _resolve_embed_model(embed_model: BaseEmbedding = None, configs: list[Any] = None) -> BaseEmbedding:
        if configs and all(isinstance(c, NoEmbedding) for c in configs):
            return MockEmbedding(embed_dim=1)

        return embed_model or get_rag_embedding()
