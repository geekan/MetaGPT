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

from metagpt.config import CONFIG
from metagpt.utils.s3 import S3


@pytest.mark.asyncio
async def test_s3():
    # Prerequisites
    assert CONFIG.S3_ACCESS_KEY and CONFIG.S3_ACCESS_KEY != "YOUR_S3_ACCESS_KEY"
    assert CONFIG.S3_SECRET_KEY and CONFIG.S3_SECRET_KEY != "YOUR_S3_SECRET_KEY"
    assert CONFIG.S3_ENDPOINT_URL and CONFIG.S3_ENDPOINT_URL != "YOUR_S3_ENDPOINT_URL"
    # assert CONFIG.S3_SECURE: true # true/false
    assert CONFIG.S3_BUCKET and CONFIG.S3_BUCKET != "YOUR_S3_BUCKET"

    conn = S3()
    assert conn.is_valid
    object_name = "unittest.bak"
    await conn.upload_file(bucket=CONFIG.S3_BUCKET, local_path=__file__, object_name=object_name)
    pathname = (Path(__file__).parent / uuid.uuid4().hex).with_suffix(".bak")
    pathname.unlink(missing_ok=True)
    await conn.download_file(bucket=CONFIG.S3_BUCKET, object_name=object_name, local_path=str(pathname))
    assert pathname.exists()
    url = await conn.get_object_url(bucket=CONFIG.S3_BUCKET, object_name=object_name)
    assert url
    bin_data = await conn.get_object(bucket=CONFIG.S3_BUCKET, object_name=object_name)
    assert bin_data
    async with aiofiles.open(__file__, mode="r", encoding="utf-8") as reader:
        data = await reader.read()
    res = await conn.cache(data, ".bak", "script")
    assert "http" in res


@pytest.mark.asyncio
async def test_s3_no_error():
    conn = S3()
    key = conn.auth_config["aws_secret_access_key"]
    conn.auth_config["aws_secret_access_key"] = ""
    try:
        res = await conn.cache("ABC", ".bak", "script")
        assert not res
    finally:
        conn.auth_config["aws_secret_access_key"] = key


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
