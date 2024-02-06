import base64
import os.path
import traceback
import uuid
from pathlib import Path
from typing import Optional

import aioboto3
import aiofiles

from metagpt.config2 import S3Config
from metagpt.const import BASE64_FORMAT
from metagpt.logs import logger


class S3:
    """A class for interacting with Amazon S3 storage."""

    def __init__(self, config: S3Config):
        self.session = aioboto3.Session()
        self.config = config
        self.auth_config = {
            "service_name": "s3",
            "aws_access_key_id": config.access_key,
            "aws_secret_access_key": config.secret_key,
            "endpoint_url": config.endpoint,
        }

    async def upload_file(
        self,
        bucket: str,
        local_path: str,
        object_name: str,
    ) -> None:
        """Upload a file from the local path to the specified path of the storage bucket specified in s3.

        Args:
            bucket: The name of the S3 storage bucket.
            local_path: The local file path, including the file name.
            object_name: The complete path of the uploaded file to be stored in S3, including the file name.

        Raises:
            Exception: If an error occurs during the upload process, an exception is raised.
        """
        try:
            async with self.session.client(**self.auth_config) as client:
                async with aiofiles.open(local_path, mode="rb") as reader:
                    body = await reader.read()
                    await client.put_object(Body=body, Bucket=bucket, Key=object_name)
                    logger.info(f"Successfully uploaded the file to path {object_name} in bucket {bucket} of s3.")
        except Exception as e:
            logger.error(f"Failed to upload the file to path {object_name} in bucket {bucket} of s3: {e}")
            raise e

    async def get_object_url(
        self,
        bucket: str,
        object_name: str,
    ) -> str:
        """Get the URL for a downloadable or preview file stored in the specified S3 bucket.

        Args:
            bucket: The name of the S3 storage bucket.
            object_name: The complete path of the file stored in S3, including the file name.

        Returns:
            The URL for the downloadable or preview file.

        Raises:
            Exception: If an error occurs while retrieving the URL, an exception is raised.
        """
        try:
            async with self.session.client(**self.auth_config) as client:
                file = await client.get_object(Bucket=bucket, Key=object_name)
                return str(file["Body"].url)
        except Exception as e:
            logger.error(f"Failed to get the url for a downloadable or preview file: {e}")
            raise e

    async def get_object(
        self,
        bucket: str,
        object_name: str,
    ) -> bytes:
        """Get the binary data of a file stored in the specified S3 bucket.

        Args:
            bucket: The name of the S3 storage bucket.
            object_name: The complete path of the file stored in S3, including the file name.

        Returns:
            The binary data of the requested file.

        Raises:
            Exception: If an error occurs while retrieving the file data, an exception is raised.
        """
        try:
            async with self.session.client(**self.auth_config) as client:
                s3_object = await client.get_object(Bucket=bucket, Key=object_name)
                return await s3_object["Body"].read()
        except Exception as e:
            logger.error(f"Failed to get the binary data of the file: {e}")
            raise e

    async def download_file(
        self, bucket: str, object_name: str, local_path: str, chunk_size: Optional[int] = 128 * 1024
    ) -> None:
        """Download an S3 object to a local file.

        Args:
            bucket: The name of the S3 storage bucket.
            object_name: The complete path of the file stored in S3, including the file name.
            local_path: The local file path where the S3 object will be downloaded.
            chunk_size: The size of data chunks to read and write at a time. Default is 128 KB.

        Raises:
            Exception: If an error occurs during the download process, an exception is raised.
        """
        try:
            async with self.session.client(**self.auth_config) as client:
                s3_object = await client.get_object(Bucket=bucket, Key=object_name)
                stream = s3_object["Body"]
                async with aiofiles.open(local_path, mode="wb") as writer:
                    while True:
                        file_data = await stream.read(chunk_size)
                        if not file_data:
                            break
                        await writer.write(file_data)
        except Exception as e:
            logger.error(f"Failed to download the file from S3: {e}")
            raise e

    async def cache(self, data: str, file_ext: str, format: str = "") -> str:
        """Save data to remote S3 and return url"""
        object_name = uuid.uuid4().hex + file_ext
        path = Path(__file__).parent
        pathname = path / object_name
        try:
            async with aiofiles.open(str(pathname), mode="wb") as file:
                data = base64.b64decode(data) if format == BASE64_FORMAT else data.encode(encoding="utf-8")
                await file.write(data)

            bucket = self.config.bucket
            object_pathname = self.config.bucket or "system"
            object_pathname += f"/{object_name}"
            object_pathname = os.path.normpath(object_pathname)
            await self.upload_file(bucket=bucket, local_path=str(pathname), object_name=object_pathname)
            pathname.unlink(missing_ok=True)

            return await self.get_object_url(bucket=bucket, object_name=object_pathname)
        except Exception as e:
            logger.exception(f"{e}, stack:{traceback.format_exc()}")
            pathname.unlink(missing_ok=True)
            return None
