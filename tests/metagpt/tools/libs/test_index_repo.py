import shutil

import pytest

from metagpt.const import DEFAULT_WORKSPACE_ROOT, TEST_DATA_PATH
from metagpt.tools.libs.index_repo import IndexRepo


@pytest.mark.asyncio
@pytest.mark.parametrize(("path", "query"), [(TEST_DATA_PATH / "requirements", "业务线")])
async def test_index_repo(path, query):
    index_path = DEFAULT_WORKSPACE_ROOT / ".index"
    repo = IndexRepo(filename=str(index_path), root_path=str(path), min_token_count=0)
    await repo.add([path])
    await repo.add([path])
    assert index_path.exists()

    rsp = await repo.search(query)
    assert rsp

    repo2 = IndexRepo(filename=str(index_path), root_path=str(path), min_token_count=0)
    rsp2 = await repo2.search(query)
    assert rsp2

    merged_rsp = await repo.merge(query=query, indices_list=[rsp, rsp2])
    assert merged_rsp

    shutil.rmtree(index_path)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
