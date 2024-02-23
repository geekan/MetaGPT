"""Simple Engine."""


from typing import Optional

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.embeddings import BaseEmbedding
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
    NodeWithScore,
    QueryBundle,
    QueryType,
    TextNode,
    TransformComponent,
)

from metagpt.rag.factories import get_rag_llm, get_rankers, get_retriever
from metagpt.rag.interface import RAGObject
from metagpt.rag.retrievers.base import ModifiableRAGRetriever
from metagpt.rag.schema import BaseRankerConfig, BaseRetrieverConfig
from metagpt.utils.embedding import get_embedding


class SimpleEngine(RetrieverQueryEngine):
    """
    SimpleEngine is a lightweight and easy-to-use search engine that integrates
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
        """This engine is designed to be simple and straightforward

        Args:
            input_dir: Path to the directory.
            input_files: List of file paths to read (Optional; overrides input_dir, exclude).
            transformations: Parse documents to nodes. Default [SentenceSplitter].
            embed_model: Parse nodes to embedding. Must supported by llama index. Default OpenAIEmbedding.
            llm: Must supported by llama index. Default OpenAI.
            retriever_configs: Configuration for retrievers. If more than one config, will use SimpleHybridRetriever.
            ranker_configs: Configuration for rankers.
        """
        documents = SimpleDirectoryReader(input_dir=input_dir, input_files=input_files).load_data()
        index = VectorStoreIndex.from_documents(
            documents=documents,
            transformations=transformations or [SentenceSplitter()],
            embed_model=embed_model or get_embedding(),
        )
        llm = llm or get_rag_llm()
        retriever = get_retriever(configs=retriever_configs, index=index)
        rankers = get_rankers(configs=ranker_configs, llm=llm)

        return cls(
            retriever=retriever,
            node_postprocessors=rankers,
            response_synthesizer=get_response_synthesizer(llm=llm),
            index=index,
        )

    async def asearch(self, content: str, **kwargs) -> str:
        """Inplement tools.SearchInterface"""
        return await self.aquery(content)

    async def aretrieve(self, query: QueryType) -> list[NodeWithScore]:
        """Allow query to be str"""
        query_bundle = QueryBundle(query) if isinstance(query, str) else query
        return await super().aretrieve(query_bundle)

    def add_docs(self, input_files: list[str]):
        """Add docs to retriever. retriever must has add_nodes func."""
        self._ensure_retriever_modifiable()

        documents = SimpleDirectoryReader(input_files=input_files).load_data()
        nodes = run_transformations(documents, transformations=self.index._transformations)
        self._save_nodes(nodes)

    def add_objs(self, objs: list[RAGObject]):
        """Adds objects to the retriever, storing each object's original form in metadata for future reference."""
        self._ensure_retriever_modifiable()

        nodes = [TextNode(text=obj.rag_key(), metadata={"obj": obj.model_dump()}) for obj in objs]
        self._save_nodes(nodes)

    def _ensure_retriever_modifiable(self):
        if not isinstance(self.retriever, ModifiableRAGRetriever):
            raise TypeError(f"the retriever is not modifiable: {type(self.retriever)}")

    def _save_nodes(self, nodes: list[BaseNode]):
        # for search in memory
        self.retriever.add_nodes(nodes)

        # for persist
        self.index.insert_nodes(nodes)
