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
import mock
import pytest

from metagpt.config import CONFIG
from metagpt.utils.common import aread
from metagpt.utils.s3 import S3


@pytest.mark.asyncio
@mock.patch("aioboto3.Session")
async def test_s3(mock_session_class):
    # Set up the mock response
    data = await aread(__file__, "utf-8")
    mock_session_object = mock.Mock()
    reader_mock = mock.AsyncMock()
    reader_mock.read.side_effect = [data.encode("utf-8"), b"", data.encode("utf-8")]
    type(reader_mock).url = mock.PropertyMock(return_value="https://mock")
    mock_client = mock.AsyncMock()
    mock_client.put_object.return_value = None
    mock_client.get_object.return_value = {"Body": reader_mock}
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_session_object.client.return_value = mock_client
    mock_session_class.return_value = mock_session_object

    # Prerequisites
    # assert CONFIG.S3_ACCESS_KEY and CONFIG.S3_ACCESS_KEY != "YOUR_S3_ACCESS_KEY"
    # assert CONFIG.S3_SECRET_KEY and CONFIG.S3_SECRET_KEY != "YOUR_S3_SECRET_KEY"
    # assert CONFIG.S3_ENDPOINT_URL and CONFIG.S3_ENDPOINT_URL != "YOUR_S3_ENDPOINT_URL"
    # assert CONFIG.S3_BUCKET and CONFIG.S3_BUCKET != "YOUR_S3_BUCKET"

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

    # Mock session env
    type(reader_mock).url = mock.PropertyMock(return_value="")
    old_options = CONFIG.options.copy()
    new_options = old_options.copy()
    new_options["S3_ACCESS_KEY"] = "YOUR_S3_ACCESS_KEY"
    CONFIG.set_context(new_options)
    try:
        conn = S3()
        assert not conn.is_valid
        res = await conn.cache("ABC", ".bak", "script")
        assert not res
    finally:
        CONFIG.set_context(old_options)

    await reader.close()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
