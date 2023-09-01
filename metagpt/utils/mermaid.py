#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/4 10:53
@Author  : alexanderwu, imjohndoe
@File    : mermaid.py
"""

from metagpt.const import PROJECT_ROOT
from metagpt.logs import logger

import requests
import base64
import os

def mermaid_to_file(mermaid_code, output_file_without_suffix):
    """suffix: jpeg/svg
    :param mermaid_code: mermaid code
    :param output_file_without_suffix: output filename
    :return: 0 if succeed, -1 if failed
    """
    encoded_string = base64.b64encode(mermaid_code.encode()).decode()

    dir_name = os.path.dirname(output_file_without_suffix)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)

    for suffix in ["svg", "png"]:
        output_file = f"{output_file_without_suffix}.{suffix}"
        path_type = "svg" if suffix == "svg" else "img"
        url = f"https://mermaid.ink/{path_type}/{encoded_string}"
        response = requests.get(url)

        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            logger.info(f"File saved to {output_file}")
        else:
            logger.warning(f"Failed to retrieve {suffix}")
            return -1

    return 0


MMC1 = """classDiagram
    class Main {
        -SearchEngine search_engine
        +main() str
    }
    class SearchEngine {
        -Index index
        -Ranking ranking
        -Summary summary
        +search(query: str) str
    }
    class Index {
        -KnowledgeBase knowledge_base
        +create_index(data: dict)
        +query_index(query: str) list
    }
    class Ranking {
        +rank_results(results: list) list
    }
    class Summary {
        +summarize_results(results: list) str
    }
    class KnowledgeBase {
        +update(data: dict)
        +fetch_data(query: str) dict
    }
    Main --> SearchEngine
    SearchEngine --> Index
    SearchEngine --> Ranking
    SearchEngine --> Summary
    Index --> KnowledgeBase"""

MMC2 = """sequenceDiagram
    participant M as Main
    participant SE as SearchEngine
    participant I as Index
    participant R as Ranking
    participant S as Summary
    participant KB as KnowledgeBase
    M->>SE: search(query)
    SE->>I: query_index(query)
    I->>KB: fetch_data(query)
    KB-->>I: return data
    I-->>SE: return results
    SE->>R: rank_results(results)
    R-->>SE: return ranked_results
    SE->>S: summarize_results(ranked_results)
    S-->>SE: return summary
    SE-->>M: return summary"""


if __name__ == "__main__":
    # logger.info(print_members(print_members))
    mermaid_to_file(MMC1, PROJECT_ROOT / "tmp/1")
    mermaid_to_file(MMC2, PROJECT_ROOT / "tmp/2")
