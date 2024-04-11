#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/6 00:41
@Author  : alexanderwu
@File    : test_chromadb_store.py
"""
from metagpt.document_store.chromadb_store import ChromaStore


# @pytest.mark.skip()
def test_chroma_store():
    """FIXME：chroma使用感觉很诡异，一用Python就挂，测试用例里也是"""
    # 创建 ChromaStore 实例，使用 'sample_collection' 集合
    document_store = ChromaStore("sample_collection_1", get_or_create=True)

    # 使用 write 方法添加多个文档
    document_store.write(
        ["This is document1", "This is document2"], [{"source": "google-docs"}, {"source": "notion"}], ["doc1", "doc2"]
    )

    # 使用 add 方法添加一个文档
    document_store.add("This is document3", {"source": "notion"}, "doc3")

    # 搜索文档
    results = document_store.search("This is a query document", n_results=3)
    assert len(results) > 0
