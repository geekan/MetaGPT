import shutil
from pathlib import Path

import pytest

from metagpt.const import DEFAULT_WORKSPACE_ROOT, TEST_DATA_PATH
from metagpt.tools.libs.index_repo import (
    CHATS_INDEX_ROOT,
    UPLOADS_INDEX_ROOT,
    IndexRepo,
)


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize(("path", "query"), [(TEST_DATA_PATH / "requirements", "业务线")])
async def test_index_repo(path, query):
    index_path = DEFAULT_WORKSPACE_ROOT / ".index"
    repo = IndexRepo(persist_path=str(index_path), root_path=str(path), min_token_count=0)
    await repo.add([path])
    await repo.add([path])
    assert index_path.exists()

    rsp = await repo.search(query)
    assert rsp

    repo2 = IndexRepo(persist_path=str(index_path), root_path=str(path), min_token_count=0)
    rsp2 = await repo2.search(query)
    assert rsp2

    merged_rsp = await repo.merge(query=query, indices_list=[rsp, rsp2])
    assert merged_rsp

    shutil.rmtree(index_path)


@pytest.mark.parametrize(
    ("paths", "path_type", "root"),
    [
        (["/data/uploads"], UPLOADS_INDEX_ROOT, "/data/uploads"),
        (["/data/uploads/"], UPLOADS_INDEX_ROOT, "/data/uploads"),
        (["/data/chats/1/1.txt"], str(Path(CHATS_INDEX_ROOT) / "1"), "/data/chats/1"),
        (["/data/chats/1/2.txt"], str(Path(CHATS_INDEX_ROOT) / "1"), "/data/chats/1"),
        (["/data/chats/2/2.txt", "/data/chats/2/2.txt"], str(Path(CHATS_INDEX_ROOT) / "2"), "/data/chats/2"),
        (["/data/chats.txt"], "other", ""),
    ],
)
def test_classify_path(paths, path_type, root):
    result, result_root = IndexRepo.find_index_repo_path(paths)
    assert path_type in set(result.keys())
    assert root == result_root.get(path_type, "")


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
