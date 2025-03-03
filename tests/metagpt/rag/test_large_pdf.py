import pytest

from metagpt.config2 import Config
from metagpt.const import TEST_DATA_PATH
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.factories.embedding import RAGEmbeddingFactory
from metagpt.utils.common import aread


@pytest.mark.skip
@pytest.mark.parametrize(
    ("knowledge_filename", "query_filename", "answer_filename"),
    [
        (
            TEST_DATA_PATH / "embedding/2.knowledge.md",
            TEST_DATA_PATH / "embedding/2.query.md",
            TEST_DATA_PATH / "embedding/2.answer.md",
        ),
        (
            TEST_DATA_PATH / "embedding/3.knowledge.md",
            TEST_DATA_PATH / "embedding/3.query.md",
            TEST_DATA_PATH / "embedding/3.answer.md",
        ),
    ],
)
@pytest.mark.asyncio
async def test_large_pdf(knowledge_filename, query_filename, answer_filename):
    Config.default(reload=True)  # `config.embedding.model = "text-embedding-ada-002"` changes the cache.

    engine = SimpleEngine.from_docs(
        input_files=[knowledge_filename],
    )

    query = await aread(filename=query_filename)
    rsp = await engine.aretrieve(query)
    assert rsp

    config = Config.default()
    config.embedding.model = "text-embedding-ada-002"
    factory = RAGEmbeddingFactory(config)
    embedding = factory.get_rag_embedding()
    answer = await aread(filename=answer_filename)
    answer_embedding = await embedding.aget_text_embedding(answer)
    similarity = 0
    for i in rsp:
        rsp_embedding = await embedding.aget_query_embedding(i.text)
        v = embedding.similarity(answer_embedding, rsp_embedding)
        similarity = max(similarity, v)

    print(similarity)
    assert similarity > 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
