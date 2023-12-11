from typing import List, Dict
from pathlib import Path
import re

from tenacity import retry, stop_after_attempt, wait_fixed

from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.actions.write_analysis_code import WriteCodeByGenerate


class MakeTools(WriteCodeByGenerate):
    DEFAULT_SYSTEM_MSG = """Please Create a very General Function Code startswith `def` from any codes you got.\n
    **Notice:
    1. Reflect on whether it meets the requirements of a general function.
    2. Refactor your code to get the most efficient implementation for large input data in the shortest amount of time.
    3. Use Google style for function annotations.
    4. Write example code by using old varibales in old code, and make sure it could be execute in the user's machine.**
    """

    def __init__(self, name: str = '', context: list[Message] = None, llm: LLM = None, workspace: str = None):
        """
        :param str name: name, defaults to ''
        :param list[Message] context: context, defaults to None
        :param LLM llm: llm, defaults to None
        :param str workspace: tools code saved file path dir, defaults to None
        """
        super().__init__(name, context, llm)
        self.workspace = workspace or str(Path(__file__).parents[1].joinpath("./tools/functions/libs/udf"))
        self.file_suffix: str = '.py'

    def parse_function_name(self, function_code: str) -> str:
        # 定义正则表达式模式
        pattern = r'\bdef\s+([a-zA-Z_]\w*)\s*\('
        # 在代码中搜索匹配的模式
        match = re.search(pattern, function_code)
        # 如果找到匹配项，则返回匹配的函数名；否则返回None
        if match:
            return match.group(1)
        else:
            return None

    def save(self, tool_code: str) -> None:
        func_name = self.parse_function_name(tool_code)
        if func_name is None:
            raise ValueError(f"No function name found in {tool_code}")
        saved_path = Path(self.workspace).joinpath(func_name+self.file_suffix)
        logger.info(f"Saved tool_code {func_name} in {str(saved_path)}.")
        saved_path.write_text(tool_code, encoding='utf-8')
        # TODO: 保存到udf中，供WriteCodeWithMakeTools使用

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def run(self, code_message: List[Message | Dict], **kwargs) -> str:
        msgs = self.process_msg(code_message)
        logger.info(f"Ask: {msgs[-1]}")
        tool_code = await self.llm.aask_code(msgs, **kwargs)
        logger.info(f"Respond: Got {tool_code} from llm.")
        self.save(tool_code['code'])
        return tool_code["code"]
