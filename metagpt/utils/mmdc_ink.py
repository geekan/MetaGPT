#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/4 16:12
@Author  : alitrack
@File    : mermaid.py
"""
import base64
from typing import List, Optional

from aiohttp import ClientError, ClientSession

from metagpt.logs import logger


async def mermaid_to_file(mermaid_code, output_file_without_suffix, suffixes: Optional[List[str]] = None):
    """Convert Mermaid code to various file formats.

    Args:
        mermaid_code (str): The Mermaid code to be converted.
        output_file_without_suffix (str): The output file name without the suffix.
        width (int, optional): The width of the output image. Defaults to 2048.
        height (int, optional): The height of the output image. Defaults to 2048.
        suffixes (Optional[List[str]], optional): The file suffixes to generate. Supports "png", "pdf", and "svg". Defaults to ["png"].

    Returns:
        int: 0 if the conversion is successful, -1 if the conversion fails.
    """
    encoded_string = base64.b64encode(mermaid_code.encode()).decode()
    suffixes = suffixes or ["png"]
    for suffix in suffixes:
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
