import re
from typing import List, Callable
from pathlib import Path

import wrapt
import textwrap
import inspect
from interpreter.interpreter import Interpreter

from metagpt.logs import logger
from metagpt.config import CONFIG
from metagpt.utils.highlight import highlight
from metagpt.actions.clone_function import CloneFunction, run_fucntion_code, run_fucntion_script
from metagpt.actions.run_code import RunCode


def extract_python_code(code: str):
    """提取代码块: 如果代码注释相同，则只保留最后一个代码块."""
    # 使用正则表达式匹配注释块和相关的代码
    pattern = r'(#\s[^\n]*)\n(.*?)(?=\n\s*#|$)'
    matches = re.findall(pattern, code, re.DOTALL)

    # 提取每个相同注释的最后一个代码块
    unique_comments = {}
    for comment, code_block in matches:
        unique_comments[comment] = code_block

    # 组装结果字符串
    result_code = '\n'.join([f"{comment}\n{code_block}" for comment, code_block in unique_comments.items()])
    header_code = code[:code.find("#")]
    code = header_code + result_code

    logger.info(f"Extract python code: \n {highlight(code)}")

    return code


class OpenCodeInterpreter(object):
    """https://github.com/KillianLucas/open-interpreter"""
    def __init__(self, auto_run: bool = True) -> None:
        interpreter = Interpreter()
        interpreter.auto_run = auto_run
        interpreter.model = CONFIG.openai_api_model or "gpt-3.5-turbo"
        interpreter.api_key = CONFIG.openai_api_key
        self.interpreter = interpreter

    def chat(self, query: str, reset: bool = True):
        if reset:
            self.interpreter.reset()
        return self.interpreter.chat(query, return_messages=True)

    @staticmethod
    def extract_function(query_respond: List, function_name: str, *, language: str = 'python',
                         function_format: str = None) -> str:
        """create a function from query_respond."""
        if language not in ('python'):
            raise NotImplementedError(f"Not support to parse language {language}!")

        # 定义函数形式
        if function_format is None:
            assert language == 'python', f"Expect python language for default function_format, but got {language}."
            function_format = """def {function_name}():\n{code}"""
        # 解析open-interpreter respond message中的代码模块
        code = [item['function_call']['parsed_arguments']['code'] for item in query_respond
                if "function_call" in item
                and "parsed_arguments" in item["function_call"]
                and 'language' in item["function_call"]['parsed_arguments']
                and item["function_call"]['parsed_arguments']['language'] == language]
        # 添加缩进
        indented_code_str = textwrap.indent("\n".join(code), ' ' * 4)
        # 按照代码注释, 返回去重后的代码
        if language == "python":
            return extract_python_code(function_format.format(function_name=function_name, code=indented_code_str))


def gen_query(func: Callable, args, kwargs) -> str:
    # 函数的注释, 也就是query的主体
    desc = func.__doc__
    signature = inspect.signature(func)
    # 获取函数wrapped的签名和入参的赋值
    bound_args = signature.bind(*args, **kwargs)
    bound_args.apply_defaults()
    query = f"{desc}, {bound_args.arguments}, If you must use a third-party package, use the most popular ones, for example: pandas, numpy, ta, ..."
    return query


def gen_template_fun(func: Callable) -> str:
    return f"def {func.__name__}{str(inspect.signature(func))}\n    # here is your code ..."


class OpenInterpreterDecorator(object):
    def __init__(self, save_code: bool = False, code_file_path: str = None, clear_code: bool = False) -> None:
        self.save_code = save_code
        self.code_file_path = code_file_path
        self.clear_code = clear_code

    def __call__(self, wrapped):
        @wrapt.decorator
        async def wrapper(wrapped: Callable, instance, args, kwargs):
            # 获取被装饰的函数名
            func_name = wrapped.__name__
            # 如果脚本在本地存在，而且不需要clearcode，则从脚本执行该函数
            if Path(self.code_file_path).is_file() and not self.clear_code:
                return run_fucntion_script(self.code_file_path, func_name, *args, **kwargs)

            # 使用open-interpreter逐步生成代码
            interpreter = OpenCodeInterpreter()
            query = gen_query(wrapped, args, kwargs)
            logger.info(f"query for OpenCodeInterpreter: \n {query}")
            respond = interpreter.chat(query)
            # 将open-interpreter逐步生成的代码组装成无入参的函数
            func_code = interpreter.extract_function(respond, func_name)
            # 把code克隆为wrapped，即保持code和wrapped函数有相同的入参和返回值类型
            template_func = gen_template_fun(wrapped)
            cf = CloneFunction()
            code = await cf.run(template_func=template_func, source_code=func_code)
            # 在终端显示生成的函数
            logger_code = highlight(code, "python")
            logger.info(f"Creating following Python function:\n{logger_code}")
            # 执行该函数
            try:
                res = run_fucntion_code(code, func_name, *args, **kwargs)
                if self.save_code:
                    cf._save(self.code_file_path, code)
            except Exception as e:
                raise Exception("Could not evaluate Python code", e)
            return res
        return wrapper(wrapped)
