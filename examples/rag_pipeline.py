"""RAG pipeline"""
import asyncio

from metagpt.const import EXAMPLE_PATH
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.schema import (
    BM25RetrieverConfig,
    FAISSRetrieverConfig,
    LLMRankerConfig,
)

DOC_PATH = EXAMPLE_PATH / "data/rag.txt"
QUESTION = "What are key qualities to be a good writer?"


def print_result(result, state="Retrieve"):
    """print retrieve or query result"""
    print("-" * 50)
    print(f"{state} Result:")

    if state == "Retrieve":
        for i, node in enumerate(result):
            print(f"{i}. {node.text[:10]}..., {node.score}")
        return

    print(result)


async def rag_pipeline():
    """This example run rag pipeline, use faiss&bm25 retriever and llm ranker, will print something like:

    Retrieve Result:
    0. Productivi..., 10.0
    1. I wrote cu..., 7.0
    2. I highly r..., 5.0
    --------------------------------------------------
    Query Result:
    Passion, adaptability, open-mindedness, creativity, discipline, and empathy are key qualities to be a good writer.
    """
    engine = SimpleEngine.from_docs(
        input_files=[DOC_PATH],
        retriever_configs=[FAISSRetrieverConfig(), BM25RetrieverConfig()],
        ranker_configs=[LLMRankerConfig()],
    )

    nodes = await engine.aretrieve(QUESTION)
    print_result(nodes, state="Retrieve")

    answer = await engine.aquery(QUESTION)
    print_result(answer, state="Query")


async def main():
    """RAG pipeline"""
    await rag_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
