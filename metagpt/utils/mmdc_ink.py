#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/4 16:12
@Author  : alitrack
@File    : mermaid.py
"""
import base64

from aiohttp import ClientError, ClientSession

from metagpt.logs import logger


async def mermaid_to_file(mermaid_code, output_file_without_suffix):
    """suffix: png/svg
    :param mermaid_code: mermaid code
    :param output_file_without_suffix: output filename without suffix
    :return: 0 if succeed, -1 if failed
    """
    encoded_string = base64.b64encode(mermaid_code.encode()).decode()

    for suffix in ["svg", "png"]:
        output_file = f"{output_file_without_suffix}.{suffix}"
        path_type = "svg" if suffix == "svg" else "img"
        url = f"https://mermaid.ink/{path_type}/{encoded_string}"
        async with ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        text = await response.content.read()
                        with open(output_file, "wb") as f:
                            f.write(text)
                        logger.info(f"Generating {output_file}..")
                    else:
                        logger.error(f"Failed to generate {output_file}")
                        return -1
            except ClientError as e:
                logger.error(f"network error: {e}")
                return -1
    return 0
