import asyncio
from fileinput import FileInput
from pathlib import Path
from typing import List, Union, Optional

from llama_index.core import Document
from llama_index.core.async_utils import run_jobs
from llama_index.core.readers.base import BaseReader
from llama_parse import ResultType

from metagpt.rag.parser.omniparse.client import OmniParseClient
from metagpt.rag.schema import OmniParseOptions, OmniParseType
from metagpt.logs import logger
from metagpt.utils.async_helper import NestAsyncio


class OmniParse(BaseReader):
    """OmniParse"""

    def __init__(
            self,
            api_key=None,
            base_url="http://localhost:8000",
            parse_options: OmniParseOptions = None
    ):
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
    def result_type(self, result_type: Union[str, ResultType]):
        if isinstance(result_type, str):
            result_type = ResultType(result_type)
        self.parse_options.result_type = result_type

    async def _aload_data(
            self,
            file_path: Union[str, bytes, Path],
            extra_info: Optional[dict] = None,
    ) -> List[Document]:
        try:
            if self.parse_type == OmniParseType.PDF:
                # 目前先只支持pdf解析
                parsed_result = await self.omniparse_client.parse_pdf(file_path)
            else:
                extra_info = extra_info or {}
                filename = extra_info.get("filename")   # 兼容字节数据要额外传filename
                parsed_result = await self.omniparse_client.parse_document(file_path, bytes_filename=filename)

            # 获取指定的结构数据
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
        docs = []
        if isinstance(file_path, (str, bytes, Path)):
            # 处理单个
            docs = await self._aload_data(file_path, extra_info)
        elif isinstance(file_path, list):
            # 并发处理多个
            parse_jobs = [self._aload_data(file_item, extra_info) for file_item in file_path]
            doc_ret_list = await run_jobs(jobs=parse_jobs, workers=self.parse_options.num_workers)
            docs = [doc for docs in doc_ret_list for doc in docs]
        return docs

    def load_data(
            self,
            file_path: Union[List[FileInput], FileInput],
            extra_info: Optional[dict] = None,
    ) -> List[Document]:
        """Load data from the input path."""
        NestAsyncio.apply_once()    # 兼容异步嵌套调用
        return asyncio.run(self.aload_data(file_path, extra_info))
