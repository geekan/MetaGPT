"""RAG pipeline"""
import asyncio

from pydantic import BaseModel

from metagpt.const import EXAMPLE_PATH
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.schema import (
    BM25RetrieverConfig,
    FAISSRetrieverConfig,
    LLMRankerConfig,
)

DOC_PATH = EXAMPLE_PATH / "data/rag_writer.txt"
QUESTION = "What are key qualities to be a good writer?"


class RAGExample:
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
        0. Bojan like..., 10.0

        Query Result:
        Bojan likes traveling.
        """
        self._print_title("RAG Add Docs")

        travel_question = "What does Bojan like? If you not sure, just answer I don't know"
        travel_filepath = EXAMPLE_PATH / "data/rag_travel.txt"

        print("[Before add docs]")
        await self.rag_pipeline(question=travel_question, print_title=False)

        print("[After add docs]")
        self.engine.add_docs([travel_filepath])
        await self.rag_pipeline(question=travel_question, print_title=False)

    async def rag_add_objs(self):
        """This example show how to add objs, before add docs engine retrieve nothing, after add objs engine give the correct answer, will print something like:
        [Before add objs]
        Retrieve Result:

        [After add objs]
        Retrieve Result:
        0. 100m Sprin..., 10.0

        [Object Detail]
        {'name': 'foo', 'goal': 'Win The Game', 'tool': 'Red Bull Energy Drink'}
        """

        self._print_title("RAG Add Docs")

        class Player(BaseModel):
            name: str = ""
            goal: str = "Win The Game"
            tool: str = "Red Bull Energy Drink"

            def rag_key(self) -> str:
                return self.goal

        foo = Player(name="foo")
        question = f"{foo.rag_key()}"

        print("[Before add objs]")
        await self._retrieve_and_print(question)

        print("[After add objs]")
        self.engine.add_objs([foo])
        nodes = await self._retrieve_and_print(question)

        print("[Object Detail]")
        player: Player = nodes[0].metadata["obj"]
        print(player)

    @staticmethod
    def _print_title(title):
        print(f"{'#'*50} {title} {'#'*50}")

    @staticmethod
    def _print_result(result, state="Retrieve"):
        """print retrieve or query result"""
        print(f"{state} Result:")

        if state == "Retrieve":
            for i, node in enumerate(result):
                print(f"{i}. {node.text[:10]}..., {node.score}")
            print()
            return

        print(f"{result}\n")

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


if __name__ == "__main__":
    asyncio.run(main())
