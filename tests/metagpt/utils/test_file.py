#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/9/4 15:40:40
@Author  : Stitch-z
@File    : test_file.py
"""
from pathlib import Path

import pytest

from metagpt.utils.file import File


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("root_path", "filename", "content"),
    [
        (
            Path(__file__).parent / "../../../workspace/unittest/data/tutorial_docx/2023-09-07_17-05-20",
            "test.md",
            "Hello World!",
        )
    ],
)
async def test_write_and_read_file(root_path: Path, filename: str, content: bytes):
    full_file_name = await File.write(root_path=root_path, filename=filename, content=content.encode("utf-8"))
    assert isinstance(full_file_name, Path)
    assert root_path / filename == full_file_name
    file_data = await File.read(full_file_name)
    assert file_data.decode("utf-8") == content


@pytest.mark.asyncio
async def test_read_chunk():
    val = await File.read(file_path=__file__, chunk_size=10)
    assert val


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
