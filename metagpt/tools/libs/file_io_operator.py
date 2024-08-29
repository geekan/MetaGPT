import base64
import os
from pathlib import Path
from typing import List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict

from metagpt.config2 import Config
from metagpt.logs import logger
from metagpt.tools.tool_registry import register_tool
from metagpt.utils import read_docx
from metagpt.utils.common import aread, aread_bin, awrite_bin, check_http_endpoint
from metagpt.utils.repo_to_markdown import is_text_file
from metagpt.utils.report import FileIOOperatorReporter


class FileBlock(BaseModel):
    """A block of content in a file"""

    file_path: str
    block_content: str


class LineNumberError(Exception):
    pass


@register_tool()
class FileOperator(BaseModel):
    """
    A state-of-state tool for reading, understanding, and writing files.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    resource: FileIOOperatorReporter = FileIOOperatorReporter()

    def write(self, path: str, content: str):
        """Write the whole content to a file. When used, make sure content arg contains the full content of the file."""
        if "\n" not in content and "\\n" in content:
            # A very raw rule to correct the content: If 'content' lacks actual newlines ('\n') but includes '\\n', consider
            # replacing them with '\n' to potentially correct mistaken representations of newline characters.
            content = content.replace("\\n", "\n")
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        # self.resource.report(path, "path")
        return f"The writing/coding the of the file {os.path.basename(path)}' is now completed. The file '{os.path.basename(path)}' has been successfully created."

    async def read(self, path: str) -> FileBlock:
        """Read the whole content of a file. Using absolute paths as the argument for specifying the file location."""
        is_text, mime_type = await is_text_file(path)
        if is_text:
            lines = await self._read_text(path)
        elif mime_type == "application/pdf":
            lines = await self._read_pdf(path)
        elif mime_type in {
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-word.document.macroEnabled.12",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
            "application/vnd.ms-word.template.macroEnabled.12",
        }:
            lines = await self._read_docx(path)
        else:
            return FileBlock(file_path=str(path), block_content="")
        self.resource.report(str(path), "path")

        lines_with_num = [f"{i + 1:03}|{line}" for i, line in enumerate(lines)]
        result = FileBlock(
            file_path=str(path),
            block_content="".join(lines_with_num),
        )
        return result

    @staticmethod
    async def _read_text(path: Union[str, Path]) -> List[str]:
        content = await aread(path)
        lines = content.split("\n")
        return lines

    @staticmethod
    async def _read_pdf(path: Union[str, Path]) -> List[str]:
        result = await FileOperator._omniparse_read_file(path)
        if result:
            return result

        from llama_index.readers.file import PDFReader

        reader = PDFReader()
        lines = reader.load_data(file=Path(path))
        return [i.text for i in lines]

    @staticmethod
    async def _read_docx(path: Union[str, Path]) -> List[str]:
        result = await FileOperator._omniparse_read_file(path)
        if result:
            return result
        return read_docx(str(path))

    @staticmethod
    async def _omniparse_read_file(path: Union[str, Path]) -> Optional[List[str]]:
        from metagpt.tools.libs import get_env_default
        from metagpt.utils.omniparse_client import OmniParseClient

        env_base_url = await get_env_default(key="base_url", app_name="OmniParse", default_value="")
        env_timeout = await get_env_default(key="timeout", app_name="OmniParse", default_value="")
        conf_base_url, conf_timeout = await FileOperator._read_omniparse_config()

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
        if not ret.images:
            return [ret.text] if ret.text else None

        result = [ret.text]
        img_dir = Path(path).parent / (Path(path).name.replace(".", "_") + "_images")
        img_dir.mkdir(parents=True, exist_ok=True)
        for i in ret.images:
            byte_data = base64.b64decode(i.image)
            filename = img_dir / i.image_name
            await awrite_bin(filename=filename, data=byte_data)
            result.append(f"![{i.image_name}]({str(filename)})")
        return result

    @staticmethod
    async def _read_omniparse_config() -> Tuple[str, int]:
        config = Config.default()
        if config.omniparse and config.omniparse.url:
            return config.omniparse.url, config.omniparse.timeout
        return "", 0
