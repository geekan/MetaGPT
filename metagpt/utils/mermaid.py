#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/4 10:53
@Author  : alexanderwu alitrack
@File    : mermaid.py
"""
import asyncio
import os
from pathlib import Path

from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.utils.common import awrite, check_cmd_exists


async def mermaid_to_file(engine, mermaid_code, output_file_without_suffix, width=2048, height=2048) -> int:
    """suffix: png/svg/pdf

    :param mermaid_code: mermaid code
    :param output_file_without_suffix: output filename
    :param width:
    :param height:
    :return: 0 if succeed, -1 if failed
    """
    # Write the Mermaid code to a temporary file
    dir_name = os.path.dirname(output_file_without_suffix)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
    tmp = Path(f"{output_file_without_suffix}.mmd")
    await awrite(filename=tmp, data=mermaid_code)

    if engine == "nodejs":
        if check_cmd_exists(config.mermaid.path) != 0:
            logger.warning(
                "RUN `npm install -g @mermaid-js/mermaid-cli` to install mmdc,"
                "or consider changing engine to `playwright`, `pyppeteer`, or `ink`."
            )
            return -1

        for suffix in ["pdf", "svg", "png"]:
            output_file = f"{output_file_without_suffix}.{suffix}"
            # Call the `mmdc` command to convert the Mermaid code to a PNG
            logger.info(f"Generating {output_file}..")

            if config.mermaid.puppeteer_config:
                commands = [
                    config.mermaid.path,
                    "-p",
                    config.mermaid.puppeteer_config,
                    "-i",
                    str(tmp),
                    "-o",
                    output_file,
                    "-w",
                    str(width),
                    "-H",
                    str(height),
                ]
            else:
                commands = [config.mermaid.path, "-i", str(tmp), "-o", output_file, "-w", str(width), "-H", str(height)]
            process = await asyncio.create_subprocess_shell(
                " ".join(commands), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            if stdout:
                logger.info(stdout.decode())
            if stderr:
                logger.warning(stderr.decode())
    else:
        if engine == "playwright":
            from metagpt.utils.mmdc_playwright import mermaid_to_file

            return await mermaid_to_file(mermaid_code, output_file_without_suffix, width, height)
        elif engine == "pyppeteer":
            from metagpt.utils.mmdc_pyppeteer import mermaid_to_file

            return await mermaid_to_file(mermaid_code, output_file_without_suffix, width, height)
        elif engine == "ink":
            from metagpt.utils.mmdc_ink import mermaid_to_file

            return await mermaid_to_file(mermaid_code, output_file_without_suffix)
        elif engine == "none":
            return 0
        else:
            logger.warning(f"Unsupported mermaid engine: {engine}")
    return 0


MMC1 = """
classDiagram
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
    Index --> KnowledgeBase
"""

MMC2 = """
sequenceDiagram
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
    SE-->>M: return summary
"""
