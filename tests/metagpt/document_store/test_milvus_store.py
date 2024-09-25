import random

import pytest

from metagpt.document_store.milvus_store import MilvusConnection, MilvusStore

seed_value = 42
random.seed(seed_value)

vectors = [[random.random() for _ in range(8)] for _ in range(10)]
ids = [f"doc_{i}" for i in range(10)]
metadata = [{"color": "red", "rand_number": i % 10} for i in range(10)]


def assert_almost_equal(actual, expected):
    delta = 1e-10
    if isinstance(expected, list):
        assert len(actual) == len(expected)
        for ac, exp in zip(actual, expected):
            assert abs(ac - exp) <= delta, f"{ac} is not within {delta} of {exp}"
    else:
        assert abs(actual - expected) <= delta, f"{actual} is not within {delta} of {expected}"


@pytest.mark.skip()  # Skip because the pymilvus dependency is not installed by default
def test_milvus_store():
    milvus_connection = MilvusConnection(uri="./milvus_local.db")
    milvus_store = MilvusStore(milvus_connection)

    collection_name = "TestCollection"
    milvus_store.create_collection(collection_name, dim=8)

    milvus_store.add(collection_name, ids, vectors, metadata)

    search_results = milvus_store.search(collection_name, query=[1.0] * 8)
    assert len(search_results) > 0
    first_result = search_results[0]
    assert first_result["id"] == "doc_0"

    search_results_with_filter = milvus_store.search(collection_name, query=[1.0] * 8, filter={"rand_number": 1})
    assert len(search_results_with_filter) > 0
    assert search_results_with_filter[0]["id"] == "doc_1"

    milvus_store.delete(collection_name, _ids=["doc_0"])
    deleted_results = milvus_store.search(collection_name, query=[1.0] * 8, limit=1)
    assert deleted_results[0]["id"] != "doc_0"

    milvus_store.client.drop_collection(collection_name)
