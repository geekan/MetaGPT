#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/9/4 15:40:40
@Author  : Stitch-z
@File    : file.py
@Describe : General file operations.
"""
import aiofiles
from pathlib import Path

from metagpt.logs import logger


class File:
    """A general util for file operations."""

    @classmethod
    async def write(cls, root_path: Path, filename: str, content: bytes) -> Path:
        """Write the file content to the local specified path.

        Args:
            root_path: The root path of file, such as "/data".
            filename: The name of file, such as "test.txt".
            content: The binary content of file.

        Returns:
            The full filename of file, such as "/data/test.txt".

        Raises:
            Exception: If an unexpected error occurs during the file writing process.
        """
        try:
            root_path.mkdir(parents=True, exist_ok=True)
            full_path = root_path / filename
            async with aiofiles.open(full_path, mode="wb") as writer:
                await writer.write(content)
                logger.info(f"Successfully write file: {full_path}")
                return full_path
        except Exception as e:
            logger.error(f"Error writing file: {e}")
            raise e