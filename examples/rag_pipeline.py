"""RAG pipeline"""
import asyncio

from metagpt.const import EXAMPLE_PATH
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.schema import (
    BM25RetrieverConfig,
    FAISSRetrieverConfig,
    LLMRankerConfig,
)

DOC_PATH = EXAMPLE_PATH / "data/rag_writer.txt"
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


def build_engine(input_files: list[str]):
    engine = SimpleEngine.from_docs(
        input_files=input_files,
        retriever_configs=[FAISSRetrieverConfig(), BM25RetrieverConfig()],
        ranker_configs=[LLMRankerConfig()],
    )
    return engine


async def rag_pipeline(engine: SimpleEngine, question=QUESTION):
    """This example run rag pipeline, use faiss&bm25 retriever and llm ranker, will print something like:

    Retrieve Result:
    0. Productivi..., 10.0
    1. I wrote cu..., 7.0
    2. I highly r..., 5.0
    --------------------------------------------------
    Query Result:
    Passion, adaptability, open-mindedness, creativity, discipline, and empathy are key qualities to be a good writer.
    """
    nodes = await engine.aretrieve(question)
    print_result(nodes, state="Retrieve")

    answer = await engine.aquery(question)
    print_result(answer, state="Query")


async def rag_add_docs(engine: SimpleEngine):
    """This example show how to add docs, before add docs llm anwser I don't know, after add docs llm give the correct answer, will print something like:

    [Before add docs]
    --------------------------------------------------
    Retrieve Result:
    --------------------------------------------------
    Query Result:
    I don't know.

    [After add docs]
    --------------------------------------------------
    Retrieve Result:
    0. Bojan like..., 10.0
    --------------------------------------------------
    Query Result:
    Bojan likes traveling.
    """
    travel_question = "What does Bojan like? If you not sure, just answer i don't know"
    travel_filepath = EXAMPLE_PATH / "data/rag_travel.txt"

    print("[Before add docs]")
    await rag_pipeline(engine, question=travel_question)

    print("\n[After add docs]")
    engine.add_docs([travel_filepath])
    await rag_pipeline(engine, question=travel_question)


async def main():
    """RAG pipeline"""
    engine = build_engine([DOC_PATH])
    await rag_pipeline(engine)
    print("#" * 100)
    await rag_add_docs(engine)


if __name__ == "__main__":
    asyncio.run(main())
