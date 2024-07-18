import mimetypes
import os
import aiofiles
import httpx
from typing import Union

from metagpt.rag.schema import OmniParsedResult


class OmniParseClient:
    """
    OmniParse Server Client
    OmniParse API Docs: https://docs.cognitivelab.in/api
    """
    ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".doc", ".docx"}
    ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac"}
    ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov"}

    def __init__(self, api_key=None, base_url="http://localhost:8000", max_timeout=120):
        """
        Args:
            api_key: 默认 None 后续可用于鉴权
            base_url: api 基础url
            max_timeout: 请求最大超时时间单位s
        """
        self.api_key = api_key
        self.base_url = base_url
        self.max_timeout = max_timeout

        self.parse_media_endpoint = "/parse_media"
        self.parse_website_endpoint = "/parse_website"
        self.parse_document_endpoint = "/parse_document"

    async def __request_parse(self, endpoint: str, files: dict = None, json: dict = None) -> dict:
        """
        请求api解析文档

        Args:
            endpoint (str): API endpoint.
            files (dict, optional): 请求文件数据.
            json (dict, optional): 请求json数据.

        Returns:
            dict: 响应的json数据
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, files=files, json=json, headers=headers, timeout=self.max_timeout)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def verify_file_ext(filelike: Union[str, bytes], allowed_file_extensions: set):
        """校验文件后缀"""
        if not filelike or isinstance(filelike, bytes):
            return
        file_ext = os.path.splitext(filelike)[1].lower()
        if file_ext not in allowed_file_extensions:
            raise ValueError("File extension must be one of {}".format(allowed_file_extensions))

    async def get_file_info(
            self,
            filelike: Union[str, bytes],
            bytes_filename: str = None,
            only_bytes=True,
    ) -> Union[bytes, tuple]:
        """
        获取文件字节信息
        Args:
            filelike: 文件数据
            bytes_filename: 通过字节数据上传需要指定文件名称，方便获取mime_type
            only_bytes: 是否只需要字节数据

        Notes:
            由于 parse_document 支持多种文件解析，需要上传文件时指定文件的mime_type

        Returns:
            [bytes, tuple]
        """
        if isinstance(filelike, str):
            filename = os.path.basename(filelike)
            async with aiofiles.open(filelike, 'rb') as file:
                file_bytes = await file.read()

            if only_bytes:
                return file_bytes

            mime_type = mimetypes.guess_type(filelike)[0]
            return filename, file_bytes, mime_type
        elif isinstance(filelike, bytes):
            if only_bytes:
                return filelike
            if not bytes_filename:
                raise ValueError("bytes_filename must be set when passing bytes")

            mime_type = mimetypes.guess_type(bytes_filename)[0]
            return bytes_filename, filelike, mime_type
        else:
            raise ValueError("filelike must be a string (file path) or bytes.")

    async def parse_document(self, filelike: Union[str, bytes], bytes_filename: str = None) -> OmniParsedResult:
        """
        解析文档类型数据（支持 ".pdf", ".ppt", ".pptx", ".doc", ".docs"）
        Args:
            filelike: 文件路径 or 文件字节数据
            bytes_filename: 字节数据名称，方便获取mime_type 用于httpx请求

        Raises
            ValueError

        Returns:
            OmniParsedResult
        """
        self.verify_file_ext(filelike, self.ALLOWED_DOCUMENT_EXTENSIONS)
        file_info = await self.get_file_info(filelike, bytes_filename, only_bytes=False)
        resp = await self.__request_parse(self.parse_document_endpoint, files={'file': file_info})
        data = OmniParsedResult(**resp)
        return data

    async def parse_pdf(self, filelike: Union[str, bytes]) -> OmniParsedResult:
        """
        解析PDF文档
        Args:
            filelike: 文件路径 or 文件字节数据

        Raises
            ValueError

        Returns:
            OmniParsedResult
        """
        self.verify_file_ext(filelike, {".pdf"})
        file_info = await self.get_file_info(filelike)
        endpoint = f"{self.parse_document_endpoint}/pdf"
        resp = await self.__request_parse(endpoint=endpoint, files={'file': file_info})
        data = OmniParsedResult(**resp)
        return data

    async def parse_video(self, filelike: Union[str, bytes], bytes_filename: str = None) -> dict:
        """解析视频"""
        self.verify_file_ext(filelike, self.ALLOWED_VIDEO_EXTENSIONS)
        file_info = await self.get_file_info(filelike, bytes_filename, only_bytes=False)
        return await self.__request_parse(f"{self.parse_media_endpoint}/video", files={'file': file_info})

    async def parse_audio(self, filelike: Union[str, bytes], bytes_filename: str = None) -> dict:
        """解析音频"""
        self.verify_file_ext(filelike, self.ALLOWED_AUDIO_EXTENSIONS)
        file_info = await self.get_file_info(filelike, bytes_filename, only_bytes=False)
        return await self.__request_parse(f"{self.parse_media_endpoint}/audio", files={'file': file_info})

    async def parse_website(self, url: str) -> dict:
        """解析网站"""
        return await self.__request_parse(self.parse_website_endpoint, json={'url': url})
