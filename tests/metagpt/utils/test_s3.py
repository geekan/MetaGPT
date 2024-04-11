#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_s3.py
"""
import uuid
from pathlib import Path

import aioboto3
import pytest

from metagpt.config2 import Config
from metagpt.configs.s3_config import S3Config
from metagpt.utils.common import aread
from metagpt.utils.s3 import S3


@pytest.mark.asyncio
async def test_s3(mocker):
    # Set up the mock response
    data = await aread(__file__, "utf-8")
    reader_mock = mocker.AsyncMock()
    reader_mock.read.side_effect = [data.encode("utf-8"), b"", data.encode("utf-8")]
    type(reader_mock).url = mocker.PropertyMock(return_value="https://mock")
    mock_client = mocker.AsyncMock()
    mock_client.put_object.return_value = None
    mock_client.get_object.return_value = {"Body": reader_mock}
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mocker.patch.object(aioboto3.Session, "client", return_value=mock_client)
    mock_config = mocker.Mock()
    mock_config.s3 = S3Config(
        access_key="mock_access_key",
        secret_key="mock_secret_key",
        endpoint="http://mock.endpoint",
        bucket="mock_bucket",
    )
    mocker.patch.object(Config, "default", return_value=mock_config)

    # Prerequisites
    s3 = Config.default().s3
    assert s3
    conn = S3(s3)
    object_name = "unittest.bak"
    await conn.upload_file(bucket=s3.bucket, local_path=__file__, object_name=object_name)
    pathname = (Path(__file__).parent / "../../../workspace/unittest" / uuid.uuid4().hex).with_suffix(".bak")
    pathname.unlink(missing_ok=True)
    await conn.download_file(bucket=s3.bucket, object_name=object_name, local_path=str(pathname))
    assert pathname.exists()
    url = await conn.get_object_url(bucket=s3.bucket, object_name=object_name)
    assert url
    bin_data = await conn.get_object(bucket=s3.bucket, object_name=object_name)
    assert bin_data
    data = await aread(filename=__file__)
    res = await conn.cache(data, ".bak", "script")
    assert "http" in res

    # Mock session env
    s3.access_key = "ABC"
    type(reader_mock).url = mocker.PropertyMock(return_value="")
    try:
        conn = S3(s3)
        res = await conn.cache("ABC", ".bak", "script")
        assert not res
    except Exception:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
