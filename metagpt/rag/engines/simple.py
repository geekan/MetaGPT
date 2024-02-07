"""Simple Engine."""


from typing import Optional

from llama_index import ServiceContext, SimpleDirectoryReader, VectorStoreIndex
from llama_index.callbacks.base import CallbackManager
from llama_index.core.base_retriever import BaseRetriever
from llama_index.embeddings.base import BaseEmbedding
from llama_index.indices.base import BaseIndex
from llama_index.llms.llm import LLM
from llama_index.postprocessor.types import BaseNodePostprocessor
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.response_synthesizers import BaseSynthesizer
from llama_index.schema import NodeWithScore, QueryBundle, QueryType

from metagpt.rag.factory import get_rankers, get_retriever
from metagpt.rag.llm import get_default_llm
from metagpt.rag.retrievers.base import ModifiableRAGRetriever
from metagpt.rag.schema import RankerConfigType, RetrieverConfigType
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
        llm: LLM = None,
        embed_model: BaseEmbedding = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
        retriever_configs: list[RetrieverConfigType] = None,
        ranker_configs: list[RankerConfigType] = None,
    ) -> "SimpleEngine":
        """This engine is designed to be simple and straightforward

        Args:
            input_dir: Path to the directory.
            input_files: List of file paths to read (Optional; overrides input_dir, exclude).
            llm: Must supported by llama index.
            embed_model: Must supported by llama index.
            chunk_size: The size of text chunks (in tokens) to split documents into for embedding.
            chunk_overlap: The number of tokens for overlapping between consecutive chunks. Helps in maintaining context continuity.
            retriever_configs: Configuration for retrievers. If more than one config, will use SimpleHybridRetriever.
            ranker_configs: Configuration for rankers.
        """
        documents = SimpleDirectoryReader(input_dir=input_dir, input_files=input_files).load_data()
        service_context = ServiceContext.from_defaults(
            llm=llm or get_default_llm(),
            embed_model=embed_model or get_embedding(),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        index = VectorStoreIndex.from_documents(documents, service_context=service_context)
        retriever = get_retriever(index, configs=retriever_configs)
        rankers = get_rankers(configs=ranker_configs, service_context=service_context)

        return cls(retriever=retriever, node_postprocessors=rankers, index=index)

    async def asearch(self, content: str, **kwargs) -> str:
        """Inplement tools.SearchInterface"""
        return await self.aquery(content)

    async def aretrieve(self, query: QueryType) -> list[NodeWithScore]:
        """Allow query to be str"""
        query_bundle = QueryBundle(query) if isinstance(query, str) else query
        return await super().aretrieve(query_bundle)

    def add_docs(self, input_files: list[str]):
        """Add docs to retriever. retriever must has add_nodes func"""
        if not isinstance(self.retriever, ModifiableRAGRetriever):
            raise TypeError(f"must be inplement to add_docs: {type(self.retriever)}")

        documents = SimpleDirectoryReader(input_files=input_files).load_data()
        nodes = self.index.service_context.node_parser.get_nodes_from_documents(documents)
        self.retriever.add_nodes(nodes)
