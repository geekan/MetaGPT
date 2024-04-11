"""RAG pipeline"""

import asyncio

from pydantic import BaseModel

from metagpt.const import DATA_PATH, EXAMPLE_DATA_PATH
from metagpt.logs import logger
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.schema import (
    ChromaIndexConfig,
    ChromaRetrieverConfig,
    ElasticsearchIndexConfig,
    ElasticsearchRetrieverConfig,
    ElasticsearchStoreConfig,
    FAISSRetrieverConfig,
    LLMRankerConfig,
)
from metagpt.utils.exceptions import handle_exception

DOC_PATH = EXAMPLE_DATA_PATH / "rag/writer.txt"
QUESTION = "What are key qualities to be a good writer?"

TRAVEL_DOC_PATH = EXAMPLE_DATA_PATH / "rag/travel.txt"
TRAVEL_QUESTION = "What does Bob like?"

LLM_TIP = "If you not sure, just answer I don't know."


class Player(BaseModel):
    """To demonstrate rag add objs."""

    name: str = ""
    goal: str = "Win The 100-meter Sprint."
    tool: str = "Red Bull Energy Drink."

    def rag_key(self) -> str:
        """For search"""
        return self.goal


class RAGExample:
    """Show how to use RAG."""

    def __init__(self, engine: SimpleEngine = None):
        self._engine = engine

    @property
    def engine(self):
        if not self._engine:
            self._engine = SimpleEngine.from_docs(
                input_files=[DOC_PATH],
                retriever_configs=[FAISSRetrieverConfig()],
                ranker_configs=[LLMRankerConfig()],
            )
        return self._engine

    @engine.setter
    def engine(self, value: SimpleEngine):
        self._engine = value

    async def run_pipeline(self, question=QUESTION, print_title=True):
        """This example run rag pipeline, use faiss retriever and llm ranker, will print something like:

        Retrieve Result:
        0. Productivi..., 10.0
        1. I wrote cu..., 7.0
        2. I highly r..., 5.0

        Query Result:
        Passion, adaptability, open-mindedness, creativity, discipline, and empathy are key qualities to be a good writer.
        """
        if print_title:
            self._print_title("Run Pipeline")

        nodes = await self.engine.aretrieve(question)
        self._print_retrieve_result(nodes)

        answer = await self.engine.aquery(question)
        self._print_query_result(answer)

    async def add_docs(self):
        """This example show how to add docs.

        Before add docs llm anwser I don't know.
        After add docs llm give the correct answer, will print something like:

        [Before add docs]
        Retrieve Result:

        Query Result:
        Empty Response

        [After add docs]
        Retrieve Result:
        0. Bob like..., 10.0

        Query Result:
        Bob likes traveling.
        """
        self._print_title("Add Docs")

        travel_question = f"{TRAVEL_QUESTION}{LLM_TIP}"
        travel_filepath = TRAVEL_DOC_PATH

        logger.info("[Before add docs]")
        await self.run_pipeline(question=travel_question, print_title=False)

        logger.info("[After add docs]")
        self.engine.add_docs([travel_filepath])
        await self.run_pipeline(question=travel_question, print_title=False)

    @handle_exception
    async def add_objects(self, print_title=True):
        """This example show how to add objects.

        Before add docs, engine retrieve nothing.
        After add objects, engine give the correct answer, will print something like:

        [Before add objs]
        Retrieve Result:

        [After add objs]
        Retrieve Result:
        0. 100m Sprin..., 10.0

        [Object Detail]
        {'name': 'Mike', 'goal': 'Win The 100-meter Sprint', 'tool': 'Red Bull Energy Drink'}
        """
        if print_title:
            self._print_title("Add Objects")

        player = Player(name="Mike")
        question = f"{player.rag_key()}"

        logger.info("[Before add objs]")
        await self._retrieve_and_print(question)

        logger.info("[After add objs]")
        self.engine.add_objs([player])

        try:
            nodes = await self._retrieve_and_print(question)

            logger.info("[Object Detail]")
            player: Player = nodes[0].metadata["obj"]
            logger.info(player.name)
        except Exception as e:
            logger.error(f"nodes is empty, llm don't answer correctly, exception: {e}")

    async def init_objects(self):
        """This example show how to from objs, will print something like:

        Same as add_objects.
        """
        self._print_title("Init Objects")

        pre_engine = self.engine
        self.engine = SimpleEngine.from_objs(retriever_configs=[FAISSRetrieverConfig()])
        await self.add_objects(print_title=False)
        self.engine = pre_engine

    async def init_and_query_chromadb(self):
        """This example show how to use chromadb. how to save and load index. will print something like:

        Query Result:
        Bob likes traveling.
        """
        self._print_title("Init And Query ChromaDB")

        # 1. save index
        output_dir = DATA_PATH / "rag"
        SimpleEngine.from_docs(
            input_files=[TRAVEL_DOC_PATH],
            retriever_configs=[ChromaRetrieverConfig(persist_path=output_dir)],
        )

        # 2. load index
        engine = SimpleEngine.from_index(index_config=ChromaIndexConfig(persist_path=output_dir))

        # 3. query
        answer = await engine.aquery(TRAVEL_QUESTION)
        self._print_query_result(answer)

    @handle_exception
    async def init_and_query_es(self):
        """This example show how to use es. how to save and load index. will print something like:

        Query Result:
        Bob likes traveling.
        """
        self._print_title("Init And Query Elasticsearch")

        # 1. create es index and save docs
        store_config = ElasticsearchStoreConfig(index_name="travel", es_url="http://127.0.0.1:9200")
        engine = SimpleEngine.from_docs(
            input_files=[TRAVEL_DOC_PATH],
            retriever_configs=[ElasticsearchRetrieverConfig(store_config=store_config)],
        )

        # 2. load index
        engine = SimpleEngine.from_index(index_config=ElasticsearchIndexConfig(store_config=store_config))

        # 3. query
        answer = await engine.aquery(TRAVEL_QUESTION)
        self._print_query_result(answer)

    @staticmethod
    def _print_title(title):
        logger.info(f"{'#'*30} {title} {'#'*30}")

    @staticmethod
    def _print_retrieve_result(result):
        """Print retrieve result."""
        logger.info("Retrieve Result:")

        for i, node in enumerate(result):
            logger.info(f"{i}. {node.text[:10]}..., {node.score}")

        logger.info("")

    @staticmethod
    def _print_query_result(result):
        """Print query result."""
        logger.info("Query Result:")

        logger.info(f"{result}\n")

    async def _retrieve_and_print(self, question):
        nodes = await self.engine.aretrieve(question)
        self._print_retrieve_result(nodes)
        return nodes


async def main():
    """RAG pipeline"""
    e = RAGExample()
    await e.run_pipeline()
    await e.add_docs()
    await e.add_objects()
    await e.init_objects()
    await e.init_and_query_chromadb()
    await e.init_and_query_es()


if __name__ == "__main__":
    asyncio.run(main())
