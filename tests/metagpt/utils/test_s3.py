#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_s3.py
"""
import uuid
from pathlib import Path

import aiofiles
import pytest

from metagpt.config2 import Config
from metagpt.utils.s3 import S3


@pytest.mark.asyncio
async def test_s3():
    # Prerequisites
    s3 = Config.default().s3
    assert s3
    conn = S3(s3)
    object_name = "unittest.bak"
    await conn.upload_file(bucket=s3.bucket, local_path=__file__, object_name=object_name)
    pathname = (Path(__file__).parent / uuid.uuid4().hex).with_suffix(".bak")
    pathname.unlink(missing_ok=True)
    await conn.download_file(bucket=s3.bucket, object_name=object_name, local_path=str(pathname))
    assert pathname.exists()
    url = await conn.get_object_url(bucket=s3.bucket, object_name=object_name)
    assert url
    bin_data = await conn.get_object(bucket=s3.bucket, object_name=object_name)
    assert bin_data
    async with aiofiles.open(__file__, mode="r", encoding="utf-8") as reader:
        data = await reader.read()
    res = await conn.cache(data, ".bak", "script")
    assert "http" in res

    # Mock session env
    s3.access_key = "ABC"
    try:
        conn = S3(s3)
        res = await conn.cache("ABC", ".bak", "script")
        assert not res
    except Exception:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
