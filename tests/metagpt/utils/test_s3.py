import os
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["bucket", "local_path", "object_name"],
    [
        (
            "agent-store",
            "/code/send18-MetaGPT/workspace/resources/SD_Output/Flappy Bird_output_0.png",
            "ui-designer/2023-09-01/1.png"
        )
    ]
)
async def test_upload_file(s3, bucket, local_path, object_name):
    await s3.upload_file(bucket=bucket, local_path=local_path, object_name=object_name)
    s3_object = await s3.get_object(bucket=bucket, object_name=object_name)
    assert s3_object
    assert isinstance(s3_object, bytes)

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["bucket", "object_name"],
    [("agent-store", "ui-designer/2023-09-01/1.png")]
)
async def test_get_object_url(s3, bucket, object_name):
    url = await s3.get_object_url(bucket=bucket, object_name=object_name)
    assert bucket in url
    assert object_name in url

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["bucket", "object_name"],
    [("agent-store", "ui-designer/2023-09-01/1.png")]
)
async def test_get_object(s3, bucket, object_name):
    s3_object = await s3.get_object(bucket=bucket, object_name=object_name)
    assert s3_object
    assert isinstance(s3_object, bytes)

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["bucket", "local_path", "object_name"],
    [
        (
                "agent-store",
                "/code/send18-MetaGPT/workspace/resources/SD_Output/Flappy Bird_output_0.png",
                "ui-designer/2023-09-01/1.png"
        )
    ]
)
async def test_download_file(s3, bucket, local_path, object_name):
    await s3.download_file(bucket=bucket, object_name=object_name, local_path=local_path)
    assert os.path.exists(local_path)