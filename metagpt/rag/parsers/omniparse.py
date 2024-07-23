import asyncio
from fileinput import FileInput
from pathlib import Path
from typing import List, Optional, Union

from llama_index.core import Document
from llama_index.core.async_utils import run_jobs
from llama_index.core.readers.base import BaseReader

from metagpt.logs import logger
from metagpt.rag.schema import OmniParseOptions, OmniParseType, ParseResultType
from metagpt.utils.async_helper import NestAsyncio
from metagpt.utils.omniparse_client import OmniParseClient


class OmniParse(BaseReader):
    """OmniParse"""

    def __init__(
        self, api_key: str = None, base_url: str = "http://localhost:8000", parse_options: OmniParseOptions = None
    ):
        """
        Args:
            api_key: Default None, can be used for authentication later.
            base_url: OmniParse Base URL for the API.
            parse_options: Optional settings for OmniParse. Default is OmniParseOptions with default values.
        """
        self.parse_options = parse_options or OmniParseOptions()
        self.omniparse_client = OmniParseClient(api_key, base_url, max_timeout=self.parse_options.max_timeout)

    @property
    def parse_type(self):
        return self.parse_options.parse_type

    @property
    def result_type(self):
        return self.parse_options.result_type

    @parse_type.setter
    def parse_type(self, parse_type: Union[str, OmniParseType]):
        if isinstance(parse_type, str):
            parse_type = OmniParseType(parse_type)
        self.parse_options.parse_type = parse_type

    @result_type.setter
    def result_type(self, result_type: Union[str, ParseResultType]):
        if isinstance(result_type, str):
            result_type = ParseResultType(result_type)
        self.parse_options.result_type = result_type

    async def _aload_data(
        self,
        file_path: Union[str, bytes, Path],
        extra_info: Optional[dict] = None,
    ) -> List[Document]:
        """
        Load data from the input file_path.

        Args:
            file_path: File path or file byte data.
            extra_info: Optional dictionary containing additional information.

        Returns:
            List[Document]
        """
        try:
            if self.parse_type == OmniParseType.PDF:
                # pdf parse
                parsed_result = await self.omniparse_client.parse_pdf(file_path)
            else:
                # other parse use omniparse_client.parse_document
                # For compatible byte data, additional filename is required
                extra_info = extra_info or {}
                filename = extra_info.get("filename")
                parsed_result = await self.omniparse_client.parse_document(file_path, bytes_filename=filename)

            # Get the specified structured data based on result_type
            content = getattr(parsed_result, self.result_type)
            docs = [
                Document(
                    text=content,
                    metadata=extra_info or {},
                )
            ]
        except Exception as e:
            logger.error(f"OMNI Parse Error: {e}")
            docs = []

        return docs

    async def aload_data(
        self,
        file_path: Union[List[FileInput], FileInput],
        extra_info: Optional[dict] = None,
    ) -> List[Document]:
        """
        Load data from the input file_path.

        Args:
            file_path: File path or file byte data.
            extra_info: Optional dictionary containing additional information.

        Notes:
            This method ultimately calls _aload_data for processing.

        Returns:
            List[Document]
        """
        docs = []
        if isinstance(file_path, (str, bytes, Path)):
            # Processing single file
            docs = await self._aload_data(file_path, extra_info)
        elif isinstance(file_path, list):
            # Concurrently process multiple files
            parse_jobs = [self._aload_data(file_item, extra_info) for file_item in file_path]
            doc_ret_list = await run_jobs(jobs=parse_jobs, workers=self.parse_options.num_workers)
            docs = [doc for docs in doc_ret_list for doc in docs]
        return docs

    def load_data(
        self,
        file_path: Union[List[FileInput], FileInput],
        extra_info: Optional[dict] = None,
    ) -> List[Document]:
        """
        Load data from the input file_path.

        Args:
            file_path: File path or file byte data.
            extra_info: Optional dictionary containing additional information.

        Notes:
            This method ultimately calls aload_data for processing.

        Returns:
            List[Document]
        """
        NestAsyncio.apply_once()  # Ensure compatibility with nested async calls
        return asyncio.run(self.aload_data(file_path, extra_info))
