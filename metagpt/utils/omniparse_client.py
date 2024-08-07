import mimetypes
import os
from pathlib import Path
from typing import Union

import httpx

from metagpt.rag.schema import OmniParsedResult
from metagpt.utils.common import aread_bin


class OmniParseClient:
    """
    OmniParse Server Client
    This client interacts with the OmniParse server to parse different types of media, documents.

    OmniParse API Documentation: https://docs.cognitivelab.in/api

    Attributes:
        ALLOWED_DOCUMENT_EXTENSIONS (set): A set of supported document file extensions.
        ALLOWED_AUDIO_EXTENSIONS (set): A set of supported audio file extensions.
        ALLOWED_VIDEO_EXTENSIONS (set): A set of supported video file extensions.
    """

    ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".doc", ".docx"}
    ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac"}
    ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov"}

    def __init__(self, api_key: str = None, base_url: str = "http://localhost:8000", max_timeout: int = 120):
        """
        Args:
            api_key: Default None, can be used for authentication later.
            base_url: Base URL for the API.
            max_timeout: Maximum request timeout in seconds.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.max_timeout = max_timeout

        self.parse_media_endpoint = "/parse_media"
        self.parse_website_endpoint = "/parse_website"
        self.parse_document_endpoint = "/parse_document"

    async def _request_parse(
        self,
        endpoint: str,
        method: str = "POST",
        files: dict = None,
        params: dict = None,
        data: dict = None,
        json: dict = None,
        headers: dict = None,
        **kwargs,
    ) -> dict:
        """
        Request OmniParse API to parse a document.

        Args:
            endpoint (str): API endpoint.
            method (str, optional): HTTP method to use. Default is "POST".
            files (dict, optional): Files to include in the request.
            params (dict, optional): Query string parameters.
            data (dict, optional): Form data to include in the request body.
            json (dict, optional): JSON data to include in the request body.
            headers (dict, optional): HTTP headers to include in the request.
            **kwargs: Additional keyword arguments for httpx.AsyncClient.request()

        Returns:
            dict: JSON response data.
        """
        url = f"{self.base_url}{endpoint}"
        method = method.upper()
        headers = headers or {}
        _headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        headers.update(**_headers)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                url=url,
                method=method,
                files=files,
                params=params,
                json=json,
                data=data,
                headers=headers,
                timeout=self.max_timeout,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()

    async def parse_document(self, file_input: Union[str, bytes, Path], bytes_filename: str = None) -> OmniParsedResult:
        """
        Parse document-type data (supports ".pdf", ".ppt", ".pptx", ".doc", ".docx").

        Args:
            file_input: File path or file byte data.
            bytes_filename: Filename for byte data, useful for determining MIME type for the HTTP request.

        Raises:
            ValueError: If the file extension is not allowed.

        Returns:
            OmniParsedResult: The result of the document parsing.
        """
        self.verify_file_ext(file_input, self.ALLOWED_DOCUMENT_EXTENSIONS, bytes_filename)
        file_info = await self.get_file_info(file_input, bytes_filename)
        resp = await self._request_parse(self.parse_document_endpoint, files={"file": file_info})
        data = OmniParsedResult(**resp)
        return data

    async def parse_pdf(self, file_input: Union[str, bytes, Path]) -> OmniParsedResult:
        """
        Parse pdf document.

        Args:
            file_input: File path or file byte data.

        Raises:
            ValueError: If the file extension is not allowed.

        Returns:
            OmniParsedResult: The result of the pdf parsing.
        """
        self.verify_file_ext(file_input, {".pdf"})
        # parse_pdf supports parsing by accepting only the byte data of the file.
        file_info = await self.get_file_info(file_input, only_bytes=True)
        endpoint = f"{self.parse_document_endpoint}/pdf"
        resp = await self._request_parse(endpoint=endpoint, files={"file": file_info})
        data = OmniParsedResult(**resp)
        return data

    async def parse_video(self, file_input: Union[str, bytes, Path], bytes_filename: str = None) -> dict:
        """
        Parse video-type data (supports ".mp4", ".mkv", ".avi", ".mov").

        Args:
            file_input: File path or file byte data.
            bytes_filename: Filename for byte data, useful for determining MIME type for the HTTP request.

        Raises:
            ValueError: If the file extension is not allowed.

        Returns:
            dict: JSON response data.
        """
        self.verify_file_ext(file_input, self.ALLOWED_VIDEO_EXTENSIONS, bytes_filename)
        file_info = await self.get_file_info(file_input, bytes_filename)
        return await self._request_parse(f"{self.parse_media_endpoint}/video", files={"file": file_info})

    async def parse_audio(self, file_input: Union[str, bytes, Path], bytes_filename: str = None) -> dict:
        """
        Parse audio-type data (supports ".mp3", ".wav", ".aac").

        Args:
            file_input: File path or file byte data.
            bytes_filename: Filename for byte data, useful for determining MIME type for the HTTP request.

        Raises:
            ValueError: If the file extension is not allowed.

        Returns:
            dict: JSON response data.
        """
        self.verify_file_ext(file_input, self.ALLOWED_AUDIO_EXTENSIONS, bytes_filename)
        file_info = await self.get_file_info(file_input, bytes_filename)
        return await self._request_parse(f"{self.parse_media_endpoint}/audio", files={"file": file_info})

    @staticmethod
    def verify_file_ext(file_input: Union[str, bytes, Path], allowed_file_extensions: set, bytes_filename: str = None):
        """
        Verify the file extension.

        Args:
            file_input: File path or file byte data.
            allowed_file_extensions: Set of allowed file extensions.
            bytes_filename: Filename to use for verification when `file_input` is byte data.

        Raises:
            ValueError: If the file extension is not allowed.

        Returns:
        """
        verify_file_path = None
        if isinstance(file_input, (str, Path)):
            verify_file_path = str(file_input)
        elif isinstance(file_input, bytes) and bytes_filename:
            verify_file_path = bytes_filename

        if not verify_file_path:
            # Do not verify if only byte data is provided
            return

        file_ext = os.path.splitext(verify_file_path)[1].lower()
        if file_ext not in allowed_file_extensions:
            raise ValueError(f"Not allowed {file_ext} File extension must be one of {allowed_file_extensions}")

    @staticmethod
    async def get_file_info(
        file_input: Union[str, bytes, Path],
        bytes_filename: str = None,
        only_bytes: bool = False,
    ) -> Union[bytes, tuple]:
        """
        Get file information.

        Args:
            file_input: File path or file byte data.
            bytes_filename: Filename to use when uploading byte data, useful for determining MIME type.
            only_bytes: Whether to return only byte data. Default is False, which returns a tuple.

        Raises:
            ValueError: If bytes_filename is not provided when file_input is bytes or if file_input is not a valid type.

        Notes:
            Since `parse_document`,`parse_video`, `parse_audio` supports parsing various file types,
            the MIME type of the file must be specified when uploading.

        Returns: [bytes, tuple]
            Returns bytes if only_bytes is True, otherwise returns a tuple (filename, file_bytes, mime_type).
        """
        if isinstance(file_input, (str, Path)):
            filename = os.path.basename(str(file_input))
            file_bytes = await aread_bin(file_input)

            if only_bytes:
                return file_bytes

            mime_type = mimetypes.guess_type(file_input)[0]
            return filename, file_bytes, mime_type
        elif isinstance(file_input, bytes):
            if only_bytes:
                return file_input
            if not bytes_filename:
                raise ValueError("bytes_filename must be set when passing bytes")

            mime_type = mimetypes.guess_type(bytes_filename)[0]
            return bytes_filename, file_input, mime_type
        else:
            raise ValueError("file_input must be a string (file path) or bytes.")
