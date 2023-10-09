import re
from typing import List, Callable, Dict
from pathlib import Path

import wrapt
import textwrap
import inspect
from interpreter.core.core import Interpreter

from metagpt.logs import logger
from metagpt.config import CONFIG
from metagpt.utils.highlight import highlight
from metagpt.actions.clone_function import CloneFunction, run_function_code, run_function_script


def extract_python_code(code: str):
    """Extract code blocks: If the code comments are the same, only the last code block is kept."""
    # Use regular expressions to match comment blocks and related code.
    pattern = r'(#\s[^\n]*)\n(.*?)(?=\n\s*#|$)'
    matches = re.findall(pattern, code, re.DOTALL)

    # Extract the last code block when encountering the same comment.
    unique_comments = {}
    for comment, code_block in matches:
        unique_comments[comment] = code_block

    # concatenate into functional form
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
        # interpreter.api_base = CONFIG.openai_api_base
        self.interpreter = interpreter

    def chat(self, query: str, reset: bool = True):
        if reset:
            self.interpreter.reset()
        return self.interpreter.chat(query)

    @staticmethod
    def extract_function(query_respond: List, function_name: str, *, language: str = 'python',
                         function_format: str = None) -> str:
        """create a function from query_respond."""
        if language not in ('python'):
            raise NotImplementedError(f"Not support to parse language {language}!")

        # set function form
        if function_format is None:
            assert language == 'python', f"Expect python language for default function_format, but got {language}."
            function_format = """def {function_name}():\n{code}"""
        # Extract the code module in the open-interpreter respond message.
        # The query_respond of open-interpreter before v0.1.4 is:
        # [{'role': 'user', 'content': your query string},
        #  {'role': 'assistant', 'content': plan from llm, 'function_call': {
        #   "name": "run_code",  "arguments": "{"language": "python", "code": code of first plan},
        #   "parsed_arguments": {"language": "python", "code": code of first plan}
        #  ...]
        if "function_call" in query_respond[1]:
            code = [item['function_call']['parsed_arguments']['code'] for item in query_respond
                    if "function_call" in item
                    and "parsed_arguments" in item["function_call"]
                    and 'language' in item["function_call"]['parsed_arguments']
                    and item["function_call"]['parsed_arguments']['language'] == language]
        # The query_respond of open-interpreter v0.1.7 is:
        # [{'role': 'user', 'message': your query string},
        #  {'role': 'assistant', 'message': plan from llm, 'language': 'python',
        #   'code': code of first plan, 'output': output of first plan code},
        #  ...]
        elif "code" in query_respond[1]:
            code = [item['code'] for item in query_respond
                    if "code" in item
                    and 'language' in item
                    and item['language'] == language]
        else:
            raise ValueError(f"Unexpect message format in query_respond: {query_respond[1].keys()}")
        # add indent.
        indented_code_str = textwrap.indent("\n".join(code), ' ' * 4)
        # Return the code after deduplication.
        if language == "python":
            return extract_python_code(function_format.format(function_name=function_name, code=indented_code_str))


def gen_query(func: Callable, args, kwargs) -> str:
    # Get the annotation of the function as part of the query.
    desc = func.__doc__
    signature = inspect.signature(func)
    # Get the signature of the wrapped function and the assignment of the input parameters as part of the query.
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

    def _have_code(self, rsp: List[Dict]):
        # Is there any code generated?
        return 'code' in rsp[1] and rsp[1]['code'] not in ("", None)

    def _is_faild_plan(self, rsp: List[Dict]):
        # is faild plan?
        func_code = OpenCodeInterpreter.extract_function(rsp, 'function')
        # If there is no more than 1 '\n', the plan execution fails.
        if isinstance(func_code, str) and func_code.count('\n') <= 1:
            return True
        return False

    def _check_respond(self, query: str, interpreter: OpenCodeInterpreter, respond: List[Dict], max_try: int = 3):
        for _ in range(max_try):
            # TODO: If no code or faild plan is generated, execute chat again, repeating no more than max_try times.
            if self._have_code(respond) and not self._is_faild_plan(respond):
                break
            elif not self._have_code(respond):
                logger.warning(f"llm did not return executable code, resend the query: \n{query}")
                respond = interpreter.chat(query)
            elif self._is_faild_plan(respond):
                logger.warning(f"llm did not generate successful plan, resend the query: \n{query}")
                respond = interpreter.chat(query)

        # Post-processing of respond
        if not self._have_code(respond):
            error_msg = f"OpenCodeInterpreter do not generate code for query: \n{query}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if self._is_faild_plan(respond):
            error_msg = f"OpenCodeInterpreter do not generate code for query: \n{query}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        return respond

    def __call__(self, wrapped):
        @wrapt.decorator
        async def wrapper(wrapped: Callable, instance, args, kwargs):
            # Get the decorated function name.
            func_name = wrapped.__name__
            # If the script exists locally and clearcode is not required, execute the function from the script.
            if self.code_file_path and Path(self.code_file_path).is_file() and not self.clear_code:
                return run_function_script(self.code_file_path, func_name, *args, **kwargs)

            # Auto run generate code by using open-interpreter.
            interpreter = OpenCodeInterpreter()
            query = gen_query(wrapped, args, kwargs)
            logger.info(f"query for OpenCodeInterpreter: \n {query}")
            respond = interpreter.chat(query)
            # Make sure the response is as expected.
            respond = self._check_respond(query, interpreter, respond, 3)
            # Assemble the code blocks generated by open-interpreter into a function without parameters.
            func_code = interpreter.extract_function(respond, func_name)
            # Clone the `func_code` into wrapped, that is,
            # keep the `func_code` and wrapped functions with the same input parameter and return value types.
            template_func = gen_template_fun(wrapped)
            cf = CloneFunction()
            code = await cf.run(template_func=template_func, source_code=func_code)
            # Display the generated function in the terminal.
            logger_code = highlight(code, "python")
            logger.info(f"Creating following Python function:\n{logger_code}")
            # execute this function.
            try:
                res = run_function_code(code, func_name, *args, **kwargs)
                if self.save_code and self.code_file_path:
                    cf._save(self.code_file_path, code)
            except Exception as e:
                logger.error(f"Could not evaluate Python code \n{logger_code}: \nError: {e}")
                raise Exception("Could not evaluate Python code", e)
            return res
        return wrapper(wrapped)
