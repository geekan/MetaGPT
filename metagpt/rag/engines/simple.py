"""Simple Engine."""

from llama_index import ServiceContext, SimpleDirectoryReader
from llama_index.embeddings.base import BaseEmbedding
from llama_index.llms.llm import LLM
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.schema import NodeWithScore, QueryBundle, QueryType

from metagpt.rag.llm import get_default_llm
from metagpt.rag.rankers import get_rankers
from metagpt.rag.retrievers import get_retriever
from metagpt.rag.schema import RankerConfig, RetrieverConfig
from metagpt.utils.embedding import get_embedding


class SimpleEngine(RetrieverQueryEngine):
    """
    SimpleEngine is a search engine that uses a vector index for retrieving documents.
    """

    @classmethod
    def from_docs(
        cls,
        input_dir: str = None,
        input_files: list = None,
        llm: LLM = None,
        embed_model: BaseEmbedding = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
        retriever_configs: list[RetrieverConfig] = None,
        ranker_configs: list[RankerConfig] = None,
    ) -> "SimpleEngine":
        """This engine is designed to be simple and straightforward

        Args:
            input_dir (str): Path to the directory.
            input_files (list): List of file paths to read
                (Optional; overrides input_dir, exclude)
        """
        documents = SimpleDirectoryReader(input_dir=input_dir, input_files=input_files).load_data()
        service_context = ServiceContext.from_defaults(
            llm=llm or get_default_llm(),
            embed_model=embed_model or get_embedding(),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        nodes = service_context.node_parser.get_nodes_from_documents(documents)
        retriever = get_retriever(nodes, configs=retriever_configs, service_context=service_context)
        rankers = get_rankers(configs=ranker_configs, service_context=service_context)

        return SimpleEngine(retriever=retriever, node_postprocessors=rankers)

    async def asearch(self, content: str, **kwargs) -> str:
        """Inplement tools.SearchInterface"""
        return await self.aquery(content)

    async def aretrieve(self, query: QueryType) -> list[NodeWithScore]:
        """Allow query to be str"""
        query_bundle = QueryBundle(query) if isinstance(query, str) else query
        return await super().aretrieve(query_bundle)
