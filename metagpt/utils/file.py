#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/9/4 15:40:40
@Author  : Stitch-z
@File    : file.py
@Describe : General file operations.
"""
import base64
from pathlib import Path
from typing import Optional, Tuple, Union

import aiofiles
from fsspec.implementations.memory import MemoryFileSystem as _MemoryFileSystem

from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.utils import read_docx
from metagpt.utils.common import aread, aread_bin, awrite_bin, check_http_endpoint
from metagpt.utils.exceptions import handle_exception
from metagpt.utils.repo_to_markdown import is_text_file


class File:
    """A general util for file operations."""

    CHUNK_SIZE = 64 * 1024

    @classmethod
    @handle_exception
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
        root_path.mkdir(parents=True, exist_ok=True)
        full_path = root_path / filename
        async with aiofiles.open(full_path, mode="wb") as writer:
            await writer.write(content)
            logger.debug(f"Successfully write file: {full_path}")
            return full_path

    @classmethod
    @handle_exception
    async def read(cls, file_path: Path, chunk_size: int = None) -> bytes:
        """Partitioning read the file content from the local specified path.

        Args:
            file_path: The full file name of file, such as "/data/test.txt".
            chunk_size: The size of each chunk in bytes (default is 64kb).

        Returns:
            The binary content of file.

        Raises:
            Exception: If an unexpected error occurs during the file reading process.
        """
        chunk_size = chunk_size or cls.CHUNK_SIZE
        async with aiofiles.open(file_path, mode="rb") as reader:
            chunks = list()
            while True:
                chunk = await reader.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
            content = b"".join(chunks)
            logger.debug(f"Successfully read file, the path of file: {file_path}")
            return content

    @staticmethod
    async def is_textual_file(filename: Union[str, Path]) -> bool:
        """Determines if a given file is a textual file.

        A file is considered a textual file if it is plain text or has a
        specific set of MIME types associated with textual formats,
        including PDF and Microsoft Word documents.

        Args:
            filename (Union[str, Path]): The path to the file to be checked.

        Returns:
            bool: True if the file is a textual file, False otherwise.
        """
        is_text, mime_type = await is_text_file(filename)
        if is_text:
            return True
        if mime_type == "application/pdf":
            return True
        if mime_type in {
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-word.document.macroEnabled.12",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
            "application/vnd.ms-word.template.macroEnabled.12",
        }:
            return True
        return False

    @staticmethod
    async def read_text_file(filename: Union[str, Path]) -> Optional[str]:
        """Read the whole content of a file. Using absolute paths as the argument for specifying the file location."""
        is_text, mime_type = await is_text_file(filename)
        if is_text:
            return await File._read_text(filename)
        if mime_type == "application/pdf":
            return await File._read_pdf(filename)
        if mime_type in {
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-word.document.macroEnabled.12",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
            "application/vnd.ms-word.template.macroEnabled.12",
        }:
            return await File._read_docx(filename)
        return None

    @staticmethod
    async def _read_text(path: Union[str, Path]) -> str:
        return await aread(path)

    @staticmethod
    async def _read_pdf(path: Union[str, Path]) -> str:
        result = await File._omniparse_read_file(path)
        if result:
            return result

        from llama_index.readers.file import PDFReader

        reader = PDFReader()
        lines = reader.load_data(file=Path(path))
        return "\n".join([i.text for i in lines])

    @staticmethod
    async def _read_docx(path: Union[str, Path]) -> str:
        result = await File._omniparse_read_file(path)
        if result:
            return result
        return "\n".join(read_docx(str(path)))

    @staticmethod
    async def _omniparse_read_file(path: Union[str, Path], auto_save_image: bool = False) -> Optional[str]:
        from metagpt.tools.libs import get_env_default
        from metagpt.utils.omniparse_client import OmniParseClient

        env_base_url = await get_env_default(key="base_url", app_name="OmniParse", default_value="")
        env_timeout = await get_env_default(key="timeout", app_name="OmniParse", default_value="")
        conf_base_url, conf_timeout = await File._read_omniparse_config()

        base_url = env_base_url or conf_base_url
        if not base_url:
            return None
        api_key = await get_env_default(key="api_key", app_name="OmniParse", default_value="")
        timeout = env_timeout or conf_timeout or 600
        try:
            timeout = int(timeout)
        except ValueError:
            timeout = 600

        try:
            if not await check_http_endpoint(url=base_url):
                logger.warning(f"{base_url}: NOT AVAILABLE")
                return None
            client = OmniParseClient(api_key=api_key, base_url=base_url, max_timeout=timeout)
            file_data = await aread_bin(filename=path)
            ret = await client.parse_document(file_input=file_data, bytes_filename=str(path))
        except (ValueError, Exception) as e:
            logger.exception(f"{path}: {e}")
            return None
        if not ret.images or not auto_save_image:
            return ret.text

        result = [ret.text]
        img_dir = Path(path).parent / (Path(path).name.replace(".", "_") + "_images")
        img_dir.mkdir(parents=True, exist_ok=True)
        for i in ret.images:
            byte_data = base64.b64decode(i.image)
            filename = img_dir / i.image_name
            await awrite_bin(filename=filename, data=byte_data)
            result.append(f"![{i.image_name}]({str(filename)})")
        return "\n".join(result)

    @staticmethod
    async def _read_omniparse_config() -> Tuple[str, int]:
        if config.omniparse and config.omniparse.base_url:
            return config.omniparse.base_url, config.omniparse.timeout
        return "", 0


class MemoryFileSystem(_MemoryFileSystem):
    @classmethod
    def _strip_protocol(cls, path):
        return super()._strip_protocol(str(path))
