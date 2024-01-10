#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/27 22:18
@Author  : alexanderwu
@File    : test_search_engine_meilisearch.py
"""
import subprocess
import time

import pytest

from metagpt.logs import logger
from metagpt.tools.search_engine_meilisearch import DataSource, MeilisearchEngine

MASTER_KEY = "116Qavl2qpCYNEJNv5-e0RC9kncev1nr1gt7ybEGVLk"


@pytest.fixture()
def search_engine_server():
    # Prerequisites
    # https://www.meilisearch.com/docs/learn/getting_started/installation
    # brew update && brew install meilisearch

    meilisearch_process = subprocess.Popen(["meilisearch", "--master-key", f"{MASTER_KEY}"], stdout=subprocess.PIPE)
    time.sleep(3)
    yield
    meilisearch_process.terminate()
    meilisearch_process.wait()


@pytest.mark.skip
def test_meilisearch(search_engine_server):
    # Prerequisites
    # https://www.meilisearch.com/docs/learn/getting_started/installation
    # brew update && brew install meilisearch

    search_engine = MeilisearchEngine(url="http://localhost:7700", token=MASTER_KEY)

    # 假设有一个名为"books"的数据源，包含要添加的文档库
    books_data_source = DataSource(name="books", url="https://example.com/books")

    # 假设有一个名为"documents"的文档库，包含要添加的文档
    documents = [
        {"id": 1, "title": "Book 1", "content": "This is the content of Book 1."},
        {"id": 2, "title": "Book 2", "content": "This is the content of Book 2."},
        {"id": 3, "title": "Book 1", "content": "This is the content of Book 1."},
        {"id": 4, "title": "Book 2", "content": "This is the content of Book 2."},
        {"id": 5, "title": "Book 1", "content": "This is the content of Book 1."},
        {"id": 6, "title": "Book 2", "content": "This is the content of Book 2."},
    ]

    # 添加文档库到搜索引擎
    search_engine.add_documents(books_data_source, documents)
    logger.info(search_engine.search("Book 1"))


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
