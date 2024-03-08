"""RAG pipeline"""

import asyncio

from pydantic import BaseModel

from metagpt.const import DATA_PATH, EXAMPLE_DATA_PATH
from metagpt.logs import logger
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.schema import (
    BM25RetrieverConfig,
    ChromaIndexConfig,
    ChromaRetrieverConfig,
    FAISSRetrieverConfig,
    LLMRankerConfig,
)

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

    def __init__(self):
        self.engine = SimpleEngine.from_docs(
            input_files=[DOC_PATH],
            retriever_configs=[FAISSRetrieverConfig(), BM25RetrieverConfig()],
            ranker_configs=[LLMRankerConfig()],
        )

    async def rag_pipeline(self, question=QUESTION, print_title=True):
        """This example run rag pipeline, use faiss&bm25 retriever and llm ranker, will print something like:

        Retrieve Result:
        0. Productivi..., 10.0
        1. I wrote cu..., 7.0
        2. I highly r..., 5.0

        Query Result:
        Passion, adaptability, open-mindedness, creativity, discipline, and empathy are key qualities to be a good writer.
        """
        if print_title:
            self._print_title("RAG Pipeline")

        nodes = await self.engine.aretrieve(question)
        self._print_result(nodes, state="Retrieve")

        answer = await self.engine.aquery(question)
        self._print_result(answer, state="Query")

    async def rag_add_docs(self):
        """This example show how to add docs, before add docs llm anwser I don't know, after add docs llm give the correct answer, will print something like:

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
        self._print_title("RAG Add Docs")

        travel_question = f"{TRAVEL_QUESTION}{LLM_TIP}"
        travel_filepath = TRAVEL_DOC_PATH

        logger.info("[Before add docs]")
        await self.rag_pipeline(question=travel_question, print_title=False)

        logger.info("[After add docs]")
        self.engine.add_docs([travel_filepath])
        await self.rag_pipeline(question=travel_question, print_title=False)

    async def rag_add_objs(self, print_title=True):
        """This example show how to add objs, before add docs engine retrieve nothing, after add objs engine give the correct answer, will print something like:
        [Before add objs]
        Retrieve Result:

        [After add objs]
        Retrieve Result:
        0. 100m Sprin..., 10.0

        [Object Detail]
        {'name': 'Mike', 'goal': 'Win The 100-meter Sprint', 'tool': 'Red Bull Energy Drink'}
        """
        if print_title:
            self._print_title("RAG Add Objs")

        player = Player(name="Mike")
        question = f"{player.rag_key()}"

        logger.info("[Before add objs]")
        await self._retrieve_and_print(question)

        logger.info("[After add objs]")
        self.engine.add_objs([player])
        nodes = await self._retrieve_and_print(question)

        logger.info("[Object Detail]")
        try:
            player: Player = nodes[0].metadata["obj"]
            logger.info(player.name)
        except Exception as e:
            logger.info(f"ERROR: nodes is empty, llm don't answer correctly, exception: {e}")

    async def rag_ini_objs(self):
        """This example show how to from objs, will print something like:

        Same as rag_add_objs
        """
        self._print_title("RAG Ini Objs")

        pre_engine = self.engine
        self.engine = SimpleEngine.from_objs(retriever_configs=[FAISSRetrieverConfig()])
        await self.rag_add_objs(print_title=False)
        self.engine = pre_engine

    async def rag_chromadb(self):
        """This example show how to use chromadb. how to save and load index. will print something like:

        Query Result:
        Bob likes traveling.
        """
        self._print_title("RAG ChromaDB")

        # save index
        output_dir = DATA_PATH / "rag"
        SimpleEngine.from_docs(
            input_files=[TRAVEL_DOC_PATH],
            retriever_configs=[ChromaRetrieverConfig(persist_path=output_dir)],
        )

        # load index
        engine = SimpleEngine.from_index(
            index_config=ChromaIndexConfig(persist_path=output_dir),
        )

        # query
        answer = engine.query(TRAVEL_QUESTION)
        self._print_result(answer, state="Query")

    @staticmethod
    def _print_title(title):
        logger.info(f"{'#'*30} {title} {'#'*30}")

    @staticmethod
    def _print_result(result, state="Retrieve"):
        """print retrieve or query result"""
        logger.info(f"{state} Result:")

        if state == "Retrieve":
            for i, node in enumerate(result):
                logger.info(f"{i}. {node.text[:10]}..., {node.score}")
            logger.info("")
            return

        logger.info(f"{result}\n")

    async def _retrieve_and_print(self, question):
        nodes = await self.engine.aretrieve(question)
        self._print_result(nodes, state="Retrieve")
        return nodes


async def main():
    """RAG pipeline"""
    e = RAGExample()
    await e.rag_pipeline()
    await e.rag_add_docs()
    await e.rag_add_objs()
    await e.rag_ini_objs()
    await e.rag_chromadb()


if __name__ == "__main__":
    asyncio.run(main())
