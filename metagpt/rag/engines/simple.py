"""Simple Engine."""


from llama_index import ServiceContext, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.base import BaseEmbedding
from llama_index.llms.llm import LLM
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.schema import NodeWithScore, QueryBundle, QueryType

from metagpt.rag.llm import get_default_llm
from metagpt.rag.rankers import get_rankers
from metagpt.rag.retrievers import get_retriever
from metagpt.rag.retrievers.base import RAGRetriever
from metagpt.rag.schema import RankerConfigType, RetrieverConfigType
from metagpt.utils.embedding import get_embedding


class SimpleEngine(RetrieverQueryEngine):
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
        index = VectorStoreIndex.from_documents(documents, service_context=service_context)
        retriever = get_retriever(index, configs=retriever_configs)
        rankers = get_rankers(configs=ranker_configs, service_context=service_context)

        return SimpleEngine(retriever=retriever, node_postprocessors=rankers)

    async def asearch(self, content: str, **kwargs) -> str:
        """Inplement tools.SearchInterface"""
        return await self.aquery(content)

    async def aretrieve(self, query: QueryType) -> list[NodeWithScore]:
        """Allow query to be str"""
        query_bundle = QueryBundle(query) if isinstance(query, str) else query
        return await super().aretrieve(query_bundle)

    def add_docs(self, input_files: list[str]):
        documents = SimpleDirectoryReader(input_files=input_files).load_data()
        retriever: RAGRetriever = self.retriever
        retriever.add_docs(documents)
