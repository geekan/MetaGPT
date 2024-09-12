import pytest

from metagpt.const import TEST_DATA_PATH
from metagpt.roles.di.data_analyst import DataAnalyst


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "filename"), [("similarity search about '有哪些需求描述？' in document ", TEST_DATA_PATH / "requirements/2.pdf")]
)
async def test_similarity_search(query, filename):
    di = DataAnalyst()
    query += f"'{str(filename)}'"

    rsp = await di.run(query)
    assert rsp


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
