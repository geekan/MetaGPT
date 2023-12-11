from typing import List, Dict
from pathlib import Path
import re

from tenacity import retry, stop_after_attempt, wait_fixed

from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.actions.write_analysis_code import WriteCodeByGenerate


class MakeTools(WriteCodeByGenerate):
    DEFAULT_SYSTEM_MSG = """Please Create a General Function Code startswith `def` from any codes you got.\n
    **Notice:1. The import statement must be written after `def`, it is very important for you.
    2. Reflect on whether it meets the requirements of function.
    3. Refactor your code to get the most efficient implementation for large input data in the shortest amount of time.
    4. Write example code by using old varibales in old code, and make sure it could be execute in the user's machine.**
    """

    def __init__(self, name: str = '', context=None, llm=None, workspace: str = None):
        super().__init__(name, context, llm)
        self.workspace = workspace or "."
        self.file_suffix = '.py'

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

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def run(self, code_message: List[Message | Dict], **kwargs) -> str:
        msgs = self.process_msg(code_message)
        logger.info(f"Ask: {msgs[-1]}")
        tool_code = await self.llm.aask_code(msgs, **kwargs)
        logger.info(f"Respond: Got {tool_code} from llm.")
        self.save(tool_code['code'])
        return tool_code["code"]
