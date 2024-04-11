#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 16:07
@Author  : alexanderwu
@File    : common.py
@Modified By: mashenquan, 2023-11-1. According to Chapter 2.2.2 of RFC 116:
        Add generic class-to-string and object-to-string conversion functionality.
@Modified By: mashenquan, 2023/11/27. Bug fix: `parse_recipient` failed to parse the recipient in certain GPT-3.5
        responses.
"""
from __future__ import annotations

import ast
import base64
import contextlib
import csv
import importlib
import inspect
import json
import mimetypes
import os
import platform
import re
import sys
import traceback
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, List, Literal, Tuple, Union
from urllib.parse import quote, unquote

import aiofiles
import chardet
import loguru
import requests
from PIL import Image
from pydantic_core import to_jsonable_python
from tenacity import RetryCallState, RetryError, _utils

from metagpt.const import MESSAGE_ROUTE_TO_ALL
from metagpt.logs import logger
from metagpt.utils.exceptions import handle_exception


def check_cmd_exists(command) -> int:
    """检查命令是否存在
    :param command: 待检查的命令
    :return: 如果命令存在，返回0，如果不存在，返回非0
    """
    if platform.system().lower() == "windows":
        check_command = "where " + command
    else:
        check_command = "command -v " + command + ' >/dev/null 2>&1 || { echo >&2 "no mermaid"; exit 1; }'
    result = os.system(check_command)
    return result


def require_python_version(req_version: Tuple) -> bool:
    if not (2 <= len(req_version) <= 3):
        raise ValueError("req_version should be (3, 9) or (3, 10, 13)")
    return bool(sys.version_info > req_version)


class OutputParser:
    @classmethod
    def parse_blocks(cls, text: str):
        # 首先根据"##"将文本分割成不同的block
        blocks = text.split("##")

        # 创建一个字典，用于存储每个block的标题和内容
        block_dict = {}

        # 遍历所有的block
        for block in blocks:
            # 如果block不为空，则继续处理
            if block.strip() != "":
                # 将block的标题和内容分开，并分别去掉前后的空白字符
                block_title, block_content = block.split("\n", 1)
                # LLM可能出错，在这里做一下修正
                if block_title[-1] == ":":
                    block_title = block_title[:-1]
                block_dict[block_title.strip()] = block_content.strip()

        return block_dict

    @classmethod
    def parse_code(cls, text: str, lang: str = "") -> str:
        pattern = rf"```{lang}.*?\s+(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            code = match.group(1)
        else:
            raise Exception
        return code

    @classmethod
    def parse_str(cls, text: str):
        text = text.split("=")[-1]
        text = text.strip().strip("'").strip('"')
        return text

    @classmethod
    def parse_file_list(cls, text: str) -> list[str]:
        # Regular expression pattern to find the tasks list.
        pattern = r"\s*(.*=.*)?(\[.*\])"

        # Extract tasks list string using regex.
        match = re.search(pattern, text, re.DOTALL)
        if match:
            tasks_list_str = match.group(2)

            # Convert string representation of list to a Python list using ast.literal_eval.
            tasks = ast.literal_eval(tasks_list_str)
        else:
            tasks = text.split("\n")
        return tasks

    @staticmethod
    def parse_python_code(text: str) -> str:
        for pattern in (r"(.*?```python.*?\s+)?(?P<code>.*)(```.*?)", r"(.*?```python.*?\s+)?(?P<code>.*)"):
            match = re.search(pattern, text, re.DOTALL)
            if not match:
                continue
            code = match.group("code")
            if not code:
                continue
            with contextlib.suppress(Exception):
                ast.parse(code)
                return code
        raise ValueError("Invalid python code")

    @classmethod
    def parse_data(cls, data):
        block_dict = cls.parse_blocks(data)
        parsed_data = {}
        for block, content in block_dict.items():
            # 尝试去除code标记
            try:
                content = cls.parse_code(text=content)
            except Exception:
                # 尝试解析list
                try:
                    content = cls.parse_file_list(text=content)
                except Exception:
                    pass
            parsed_data[block] = content
        return parsed_data

    @staticmethod
    def extract_content(text, tag="CONTENT"):
        # Use regular expression to extract content between [CONTENT] and [/CONTENT]
        extracted_content = re.search(rf"\[{tag}\](.*?)\[/{tag}\]", text, re.DOTALL)

        if extracted_content:
            return extracted_content.group(1).strip()
        else:
            raise ValueError(f"Could not find content between [{tag}] and [/{tag}]")

    @classmethod
    def parse_data_with_mapping(cls, data, mapping):
        if "[CONTENT]" in data:
            data = cls.extract_content(text=data)
        block_dict = cls.parse_blocks(data)
        parsed_data = {}
        for block, content in block_dict.items():
            # 尝试去除code标记
            try:
                content = cls.parse_code(text=content)
            except Exception:
                pass
            typing_define = mapping.get(block, None)
            if isinstance(typing_define, tuple):
                typing = typing_define[0]
            else:
                typing = typing_define
            if typing == List[str] or typing == List[Tuple[str, str]] or typing == List[List[str]]:
                # 尝试解析list
                try:
                    content = cls.parse_file_list(text=content)
                except Exception:
                    pass
            # TODO: 多余的引号去除有风险，后期再解决
            # elif typing == str:
            #     # 尝试去除多余的引号
            #     try:
            #         content = cls.parse_str(text=content)
            #     except Exception:
            #         pass
            parsed_data[block] = content
        return parsed_data

    @classmethod
    def extract_struct(cls, text: str, data_type: Union[type(list), type(dict)]) -> Union[list, dict]:
        """Extracts and parses a specified type of structure (dictionary or list) from the given text.
        The text only contains a list or dictionary, which may have nested structures.

        Args:
            text: The text containing the structure (dictionary or list).
            data_type: The data type to extract, can be "list" or "dict".

        Returns:
            - If extraction and parsing are successful, it returns the corresponding data structure (list or dictionary).
            - If extraction fails or parsing encounters an error, it throw an exception.

        Examples:
            >>> text = 'xxx [1, 2, ["a", "b", [3, 4]], {"x": 5, "y": [6, 7]}] xxx'
            >>> result_list = OutputParser.extract_struct(text, "list")
            >>> print(result_list)
            >>> # Output: [1, 2, ["a", "b", [3, 4]], {"x": 5, "y": [6, 7]}]

            >>> text = 'xxx {"x": 1, "y": {"a": 2, "b": {"c": 3}}} xxx'
            >>> result_dict = OutputParser.extract_struct(text, "dict")
            >>> print(result_dict)
            >>> # Output: {"x": 1, "y": {"a": 2, "b": {"c": 3}}}
        """
        # Find the first "[" or "{" and the last "]" or "}"
        start_index = text.find("[" if data_type is list else "{")
        end_index = text.rfind("]" if data_type is list else "}")

        if start_index != -1 and end_index != -1:
            # Extract the structure part
            structure_text = text[start_index : end_index + 1]

            try:
                # Attempt to convert the text to a Python data type using ast.literal_eval
                result = ast.literal_eval(structure_text)

                # Ensure the result matches the specified data type
                if isinstance(result, (list, dict)):
                    return result

                raise ValueError(f"The extracted structure is not a {data_type}.")

            except (ValueError, SyntaxError) as e:
                raise Exception(f"Error while extracting and parsing the {data_type}: {e}")
        else:
            logger.error(f"No {data_type} found in the text.")
            return [] if data_type is list else {}


class CodeParser:
    @classmethod
    def parse_block(cls, block: str, text: str) -> str:
        blocks = cls.parse_blocks(text)
        for k, v in blocks.items():
            if block in k:
                return v
        return ""

    @classmethod
    def parse_blocks(cls, text: str):
        # 首先根据"##"将文本分割成不同的block
        blocks = text.split("##")

        # 创建一个字典，用于存储每个block的标题和内容
        block_dict = {}

        # 遍历所有的block
        for block in blocks:
            # 如果block不为空，则继续处理
            if block.strip() == "":
                continue
            if "\n" not in block:
                block_title = block
                block_content = ""
            else:
                # 将block的标题和内容分开，并分别去掉前后的空白字符
                block_title, block_content = block.split("\n", 1)
            block_dict[block_title.strip()] = block_content.strip()

        return block_dict

    @classmethod
    def parse_code(cls, block: str, text: str, lang: str = "") -> str:
        if block:
            text = cls.parse_block(block, text)
        pattern = rf"```{lang}.*?\s+(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            code = match.group(1)
        else:
            logger.error(f"{pattern} not match following text:")
            logger.error(text)
            # raise Exception
            return text  # just assume original text is code
        return code

    @classmethod
    def parse_str(cls, block: str, text: str, lang: str = ""):
        code = cls.parse_code(block, text, lang)
        code = code.split("=")[-1]
        code = code.strip().strip("'").strip('"')
        return code

    @classmethod
    def parse_file_list(cls, block: str, text: str, lang: str = "") -> list[str]:
        # Regular expression pattern to find the tasks list.
        code = cls.parse_code(block, text, lang)
        # print(code)
        pattern = r"\s*(.*=.*)?(\[.*\])"

        # Extract tasks list string using regex.
        match = re.search(pattern, code, re.DOTALL)
        if match:
            tasks_list_str = match.group(2)

            # Convert string representation of list to a Python list using ast.literal_eval.
            tasks = ast.literal_eval(tasks_list_str)
        else:
            raise Exception
        return tasks


class NoMoneyException(Exception):
    """Raised when the operation cannot be completed due to insufficient funds"""

    def __init__(self, amount, message="Insufficient funds"):
        self.amount = amount
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} -> Amount required: {self.amount}"


def print_members(module, indent=0):
    """
    https://stackoverflow.com/questions/1796180/how-can-i-get-a-list-of-all-classes-within-current-module-in-python
    """
    prefix = " " * indent
    for name, obj in inspect.getmembers(module):
        print(name, obj)
        if inspect.isclass(obj):
            print(f"{prefix}Class: {name}")
            # print the methods within the class
            if name in ["__class__", "__base__"]:
                continue
            print_members(obj, indent + 2)
        elif inspect.isfunction(obj):
            print(f"{prefix}Function: {name}")
        elif inspect.ismethod(obj):
            print(f"{prefix}Method: {name}")


def get_function_schema(func: Callable) -> dict[str, Union[dict, Any, str]]:
    sig = inspect.signature(func)
    parameters = sig.parameters
    return_type = sig.return_annotation
    param_schema = {name: parameter.annotation for name, parameter in parameters.items()}
    return {"input_params": param_schema, "return_type": return_type, "func_desc": func.__doc__, "func": func}


def parse_recipient(text):
    # FIXME: use ActionNode instead.
    pattern = r"## Send To:\s*([A-Za-z]+)\s*?"  # hard code for now
    recipient = re.search(pattern, text)
    if recipient:
        return recipient.group(1)
    pattern = r"Send To:\s*([A-Za-z]+)\s*?"
    recipient = re.search(pattern, text)
    if recipient:
        return recipient.group(1)
    return ""


def remove_comments(code_str: str) -> str:
    """Remove comments from code."""
    pattern = r"(\".*?\"|\'.*?\')|(\#.*?$)"

    def replace_func(match):
        if match.group(2) is not None:
            return ""
        else:
            return match.group(1)

    clean_code = re.sub(pattern, replace_func, code_str, flags=re.MULTILINE)
    clean_code = os.linesep.join([s.rstrip() for s in clean_code.splitlines() if s.strip()])
    return clean_code


def get_class_name(cls) -> str:
    """Return class name"""
    return f"{cls.__module__}.{cls.__name__}"


def any_to_str(val: Any) -> str:
    """Return the class name or the class name of the object, or 'val' if it's a string type."""
    if isinstance(val, str):
        return val
    elif not callable(val):
        return get_class_name(type(val))
    else:
        return get_class_name(val)


def any_to_str_set(val) -> set:
    """Convert any type to string set."""
    res = set()

    # Check if the value is iterable, but not a string (since strings are technically iterable)
    if isinstance(val, (dict, list, set, tuple)):
        # Special handling for dictionaries to iterate over values
        if isinstance(val, dict):
            val = val.values()

        for i in val:
            res.add(any_to_str(i))
    else:
        res.add(any_to_str(val))

    return res


def is_send_to(message: "Message", addresses: set):
    """Return whether it's consumer"""
    if MESSAGE_ROUTE_TO_ALL in message.send_to:
        return True

    for i in addresses:
        if i in message.send_to:
            return True
    return False


def any_to_name(val):
    """
    Convert a value to its name by extracting the last part of the dotted path.
    """
    return any_to_str(val).split(".")[-1]


def concat_namespace(*args, delimiter: str = ":") -> str:
    """Concatenate fields to create a unique namespace prefix.

    Example:
        >>> concat_namespace('prefix', 'field1', 'field2', delimiter=":")
        'prefix:field1:field2'
    """
    return delimiter.join(str(value) for value in args)


def split_namespace(ns_class_name: str, delimiter: str = ":", maxsplit: int = 1) -> List[str]:
    """Split a namespace-prefixed name into its namespace-prefix and name parts.

    Example:
        >>> split_namespace('prefix:classname')
        ['prefix', 'classname']

        >>> split_namespace('prefix:module:class', delimiter=":", maxsplit=2)
        ['prefix', 'module', 'class']
    """
    return ns_class_name.split(delimiter, maxsplit=maxsplit)


def auto_namespace(name: str, delimiter: str = ":") -> str:
    """Automatically handle namespace-prefixed names.

    If the input name is empty, returns a default namespace prefix and name.
    If the input name is not namespace-prefixed, adds a default namespace prefix.
    Otherwise, returns the input name unchanged.

    Example:
        >>> auto_namespace('classname')
        '?:classname'

        >>> auto_namespace('prefix:classname')
        'prefix:classname'

        >>> auto_namespace('')
        '?:?'

        >>> auto_namespace('?:custom')
        '?:custom'
    """
    if not name:
        return f"?{delimiter}?"
    v = split_namespace(name, delimiter=delimiter)
    if len(v) < 2:
        return f"?{delimiter}{name}"
    return name


def add_affix(text: str, affix: Literal["brace", "url", "none"] = "brace"):
    """Add affix to encapsulate data.

    Example:
        >>> add_affix("data", affix="brace")
        '{data}'

        >>> add_affix("example.com", affix="url")
        '%7Bexample.com%7D'

        >>> add_affix("text", affix="none")
        'text'
    """
    mappings = {
        "brace": lambda x: "{" + x + "}",
        "url": lambda x: quote("{" + x + "}"),
    }
    encoder = mappings.get(affix, lambda x: x)
    return encoder(text)


def remove_affix(text, affix: Literal["brace", "url", "none"] = "brace"):
    """Remove affix to extract encapsulated data.

    Args:
        text (str): The input text with affix to be removed.
        affix (str, optional): The type of affix used. Defaults to "brace".
            Supported affix types: "brace" for removing curly braces, "url" for URL decoding within curly braces.

    Returns:
        str: The text with affix removed.

    Example:
        >>> remove_affix('{data}', affix="brace")
        'data'

        >>> remove_affix('%7Bexample.com%7D', affix="url")
        'example.com'

        >>> remove_affix('text', affix="none")
        'text'
    """
    mappings = {"brace": lambda x: x[1:-1], "url": lambda x: unquote(x)[1:-1]}
    decoder = mappings.get(affix, lambda x: x)
    return decoder(text)


def general_after_log(i: "loguru.Logger", sec_format: str = "%0.3f") -> Callable[["RetryCallState"], None]:
    """
    Generates a logging function to be used after a call is retried.

    This generated function logs an error message with the outcome of the retried function call. It includes
    the name of the function, the time taken for the call in seconds (formatted according to `sec_format`),
    the number of attempts made, and the exception raised, if any.

    :param i: A Logger instance from the loguru library used to log the error message.
    :param sec_format: A string format specifier for how to format the number of seconds since the start of the call.
                       Defaults to three decimal places.
    :return: A callable that accepts a RetryCallState object and returns None. This callable logs the details
             of the retried call.
    """

    def log_it(retry_state: "RetryCallState") -> None:
        # If the function name is not known, default to "<unknown>"
        if retry_state.fn is None:
            fn_name = "<unknown>"
        else:
            # Retrieve the callable's name using a utility function
            fn_name = _utils.get_callback_name(retry_state.fn)

        # Log an error message with the function name, time since start, attempt number, and the exception
        i.error(
            f"Finished call to '{fn_name}' after {sec_format % retry_state.seconds_since_start}(s), "
            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it. "
            f"exp: {retry_state.outcome.exception()}"
        )

    return log_it


def read_json_file(json_file: str, encoding="utf-8") -> list[Any]:
    if not Path(json_file).exists():
        raise FileNotFoundError(f"json_file: {json_file} not exist, return []")

    with open(json_file, "r", encoding=encoding) as fin:
        try:
            data = json.load(fin)
        except Exception:
            raise ValueError(f"read json file: {json_file} failed")
    return data


def write_json_file(json_file: str, data: list, encoding: str = None, indent: int = 4):
    folder_path = Path(json_file).parent
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    with open(json_file, "w", encoding=encoding) as fout:
        json.dump(data, fout, ensure_ascii=False, indent=indent, default=to_jsonable_python)


def read_csv_to_list(curr_file: str, header=False, strip_trail=True):
    """
    Reads in a csv file to a list of list. If header is True, it returns a
    tuple with (header row, all rows)
    ARGS:
      curr_file: path to the current csv file.
    RETURNS:
      List of list where the component lists are the rows of the file.
    """
    logger.debug(f"start read csv: {curr_file}")
    analysis_list = []
    with open(curr_file) as f_analysis_file:
        data_reader = csv.reader(f_analysis_file, delimiter=",")
        for count, row in enumerate(data_reader):
            if strip_trail:
                row = [i.strip() for i in row]
            analysis_list += [row]
    if not header:
        return analysis_list
    else:
        return analysis_list[0], analysis_list[1:]


def import_class(class_name: str, module_name: str) -> type:
    module = importlib.import_module(module_name)
    a_class = getattr(module, class_name)
    return a_class


def import_class_inst(class_name: str, module_name: str, *args, **kwargs) -> object:
    a_class = import_class(class_name, module_name)
    class_inst = a_class(*args, **kwargs)
    return class_inst


def format_trackback_info(limit: int = 2):
    return traceback.format_exc(limit=limit)


def serialize_decorator(func):
    async def wrapper(self, *args, **kwargs):
        try:
            result = await func(self, *args, **kwargs)
            return result
        except KeyboardInterrupt:
            logger.error(f"KeyboardInterrupt occurs, start to serialize the project, exp:\n{format_trackback_info()}")
        except Exception:
            logger.error(f"Exception occurs, start to serialize the project, exp:\n{format_trackback_info()}")
        self.serialize()  # Team.serialize

    return wrapper


def role_raise_decorator(func):
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except KeyboardInterrupt as kbi:
            logger.error(f"KeyboardInterrupt: {kbi} occurs, start to serialize the project")
            if self.latest_observed_msg:
                self.rc.memory.delete(self.latest_observed_msg)
            # raise again to make it captured outside
            raise Exception(format_trackback_info(limit=None))
        except Exception as e:
            if self.latest_observed_msg:
                logger.warning(
                    "There is a exception in role's execution, in order to resume, "
                    "we delete the newest role communication message in the role's memory."
                )
                # remove role newest observed msg to make it observed again
                self.rc.memory.delete(self.latest_observed_msg)
            # raise again to make it captured outside
            if isinstance(e, RetryError):
                last_error = e.last_attempt._exception
                name = any_to_str(last_error)
                if re.match(r"^openai\.", name) or re.match(r"^httpx\.", name):
                    raise last_error

            raise Exception(format_trackback_info(limit=None))

    return wrapper


@handle_exception
async def aread(filename: str | Path, encoding="utf-8") -> str:
    """Read file asynchronously."""
    try:
        async with aiofiles.open(str(filename), mode="r", encoding=encoding) as reader:
            content = await reader.read()
    except UnicodeDecodeError:
        async with aiofiles.open(str(filename), mode="rb") as reader:
            raw = await reader.read()
            result = chardet.detect(raw)
            detected_encoding = result["encoding"]
            content = raw.decode(detected_encoding)
    return content


async def awrite(filename: str | Path, data: str, encoding="utf-8"):
    """Write file asynchronously."""
    pathname = Path(filename)
    pathname.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(str(pathname), mode="w", encoding=encoding) as writer:
        await writer.write(data)


async def read_file_block(filename: str | Path, lineno: int, end_lineno: int):
    if not Path(filename).exists():
        return ""
    lines = []
    async with aiofiles.open(str(filename), mode="r") as reader:
        ix = 0
        while ix < end_lineno:
            ix += 1
            line = await reader.readline()
            if ix < lineno:
                continue
            if ix > end_lineno:
                break
            lines.append(line)
    return "".join(lines)


def list_files(root: str | Path) -> List[Path]:
    files = []
    try:
        directory_path = Path(root)
        if not directory_path.exists():
            return []
        for file_path in directory_path.iterdir():
            if file_path.is_file():
                files.append(file_path)
            else:
                subfolder_files = list_files(root=file_path)
                files.extend(subfolder_files)
    except Exception as e:
        logger.error(f"Error: {e}")
    return files


def parse_json_code_block(markdown_text: str) -> List[str]:
    json_blocks = (
        re.findall(r"```json(.*?)```", markdown_text, re.DOTALL) if "```json" in markdown_text else [markdown_text]
    )

    return [v.strip() for v in json_blocks]


def remove_white_spaces(v: str) -> str:
    return re.sub(r"(?<!['\"])\s|(?<=['\"])\s", "", v)


async def aread_bin(filename: str | Path) -> bytes:
    """Read binary file asynchronously.

    Args:
        filename (Union[str, Path]): The name or path of the file to be read.

    Returns:
        bytes: The content of the file as bytes.

    Example:
        >>> content = await aread_bin('example.txt')
        b'This is the content of the file.'

        >>> content = await aread_bin(Path('example.txt'))
        b'This is the content of the file.'
    """
    async with aiofiles.open(str(filename), mode="rb") as reader:
        content = await reader.read()
    return content


async def awrite_bin(filename: str | Path, data: bytes):
    """Write binary file asynchronously.

    Args:
        filename (Union[str, Path]): The name or path of the file to be written.
        data (bytes): The binary data to be written to the file.

    Example:
        >>> await awrite_bin('output.bin', b'This is binary data.')

        >>> await awrite_bin(Path('output.bin'), b'Another set of binary data.')
    """
    pathname = Path(filename)
    pathname.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(str(pathname), mode="wb") as writer:
        await writer.write(data)


def is_coroutine_func(func: Callable) -> bool:
    return inspect.iscoroutinefunction(func)


def load_mc_skills_code(skill_names: list[str] = None, skills_dir: Path = None) -> list[str]:
    """load minecraft skill from js files"""
    if not skills_dir:
        skills_dir = Path(__file__).parent.absolute()
    if skill_names is None:
        skill_names = [skill[:-3] for skill in os.listdir(f"{skills_dir}") if skill.endswith(".js")]
    skills = [skills_dir.joinpath(f"{skill_name}.js").read_text() for skill_name in skill_names]
    return skills


def encode_image(image_path_or_pil: Union[Path, Image], encoding: str = "utf-8") -> str:
    """encode image from file or PIL.Image into base64"""
    if isinstance(image_path_or_pil, Image.Image):
        buffer = BytesIO()
        image_path_or_pil.save(buffer, format="JPEG")
        bytes_data = buffer.getvalue()
    else:
        if not image_path_or_pil.exists():
            raise FileNotFoundError(f"{image_path_or_pil} not exists")
        with open(str(image_path_or_pil), "rb") as image_file:
            bytes_data = image_file.read()
    return base64.b64encode(bytes_data).decode(encoding)


def decode_image(img_url_or_b64: str) -> Image:
    """decode image from url or base64 into PIL.Image"""
    if img_url_or_b64.startswith("http"):
        # image http(s) url
        resp = requests.get(img_url_or_b64)
        img = Image.open(BytesIO(resp.content))
    else:
        # image b64_json
        b64_data = re.sub("^data:image/.+;base64,", "", img_url_or_b64)
        img_data = BytesIO(base64.b64decode(b64_data))
        img = Image.open(img_data)
    return img


def log_and_reraise(retry_state: RetryCallState):
    logger.error(f"Retry attempts exhausted. Last exception: {retry_state.outcome.exception()}")
    logger.warning(
        """
Recommend going to https://deepwisdom.feishu.cn/wiki/MsGnwQBjiif9c3koSJNcYaoSnu4#part-XdatdVlhEojeAfxaaEZcMV3ZniQ
See FAQ 5.8
"""
    )
    raise retry_state.outcome.exception()


def get_markdown_codeblock_type(filename: str) -> str:
    """Return the markdown code-block type corresponding to the file extension."""
    mime_type, _ = mimetypes.guess_type(filename)
    mappings = {
        "text/x-shellscript": "bash",
        "text/x-c++src": "cpp",
        "text/css": "css",
        "text/html": "html",
        "text/x-java": "java",
        "application/javascript": "javascript",
        "application/json": "json",
        "text/x-python": "python",
        "text/x-ruby": "ruby",
        "application/sql": "sql",
    }
    return mappings.get(mime_type, "text")
