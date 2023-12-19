import ast
import os
import re
import yaml
import inspect
import importlib
from pathlib import Path
from typing import Dict, List
from metagpt.logs import logger


def extract_function_signatures(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        source_code = file.read()

    tree = ast.parse(source_code)
    function_signatures = []
    function_returns = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # 只提取用户自定义函数，排除内置函数
            if not (node.name.startswith('__') and node.name.endswith('__')):
                # 获取函数名
                function_name = node.name
                # 获取参数列表
                args = [arg.arg for arg in node.args.args]
                # 获取函数签名
                function_signature = f"{function_name}({', '.join(args)})"
                # 导入函数
                module_name = Path(file_path).parts[-1][:-len(Path(file_path).suffix)]
                module = importlib.import_module(f"metagpt.tools.functions.libs.udf.{module_name}")
                # 获取函数注释和函数路径
                function_schema = {'udf_name': function_signature,
                                   'udf_path': f'from metagpt.tools.functions.libs.udf.{module_name} import {function_name}',
                                   'udf_doc': inspect.getdoc(getattr(module, function_name))}
                function_signatures.append(function_schema)
                # 获取函数返回变量名
                source_lines, _ = inspect.getsourcelines(getattr(module, function_name))
                for line in source_lines:
                    if line.strip().startswith("return "):
                        function_returns.append({
                            'udf_name': function_name,
                            'udf_returns': [var.strip() for var in line.strip()[len("return "):].split(',')]
                        })
                        break
    return function_signatures, function_returns


def get_function_signatures_in_folder(folder_path):
    python_files = [f for f in os.listdir(folder_path) if f.endswith('.py')]
    all_function_signatures = []
    all_function_returns = []

    for file_name in python_files:
        file_path = os.path.join(folder_path, file_name)
        function_signatures, function_returns = extract_function_signatures(file_path)
        all_function_signatures.extend(function_signatures)
        all_function_returns.extend(function_returns)
    return all_function_signatures, all_function_returns


# TODO: Create Tools Yaml Style Schema
def docstring_to_yaml(docstring: str, return_vars: List[str] = None):
    logger.debug(f"\n\nFunction Docstring: \n{'-'*60}\n {docstring} \n\nFunction Returns: \n{'-'*60}\n{return_vars}\n")
    if docstring is None:
        return {}
    # 匹配简介部分
    description_match = re.search(r'^(.*?)(?:Args:|Returns:|Raises:|$)', docstring, re.DOTALL)
    description = description_match.group(1).strip() if description_match else ""

    # 匹配Args部分
    args_match = re.search(r'Args:\s*(.*?)(?:Returns:|Raises:|$)', docstring, re.DOTALL)
    _args = args_match.group(1).strip() if args_match else ""
    variable_pattern = re.compile(r'(\w+)\s*\((.*?)\):\s*(.*)')
    params = variable_pattern.findall(_args)
    if not params:
        err_msg = f"No Args found in docstring as following, Please make sure it is google style\
            : \n\n{'-'*60}\n{docstring}\n{'-'*60}\n\n."
        logger.error(err_msg)
        params = ((None, None, None),)
    # 匹配Returns部分
    returns_match = re.search(r'Returns:\s*(.*?)(?:Raises:|$)', docstring, re.DOTALL)
    returns = returns_match.group(1).strip() if returns_match else ""
    return_pattern = re.compile(r'^(.*)\s*:\s*(.*)$')
    # 添加返回值变量名
    return_vars = return_vars if isinstance(return_vars, list) else [return_vars]
    returns = [(r, *r_desc) for r_desc, r in zip(return_pattern.findall(returns), return_vars)]
    # 构建YAML字典
    yaml_data = {
        'description': description.strip('.').strip(),
        'parameters': {
            'properties': {param[0]: {'type': param[1], 'description': param[2]} for param in params if param[0] is not None},
            'required': [param[0] for param in params if param[0] is not None]
        },
        'returns': {ret[0]: {'type': ret[1], 'description': ret[2]} for ret in returns}
    }
    return yaml_data


def extract_function_schema_yaml_in_folder(folder_path: str):
    function_signatures, function_returns = get_function_signatures_in_folder(folder_path)
    function_schema_yaml_data = {}
    for func_docstring, func_returns in zip(function_signatures, function_returns):
        if func_docstring['udf_doc']:
            fun_yaml_data = docstring_to_yaml(func_docstring['udf_doc'], func_returns['udf_returns'])
            fun_yaml_data.update({'type': 'function'})
            function_schema_yaml_data.update({func_returns['udf_name']: fun_yaml_data})
    return yaml.dump(function_schema_yaml_data, default_flow_style=False)


folder_path = str(Path(__file__).parent.absolute())
function_signatures, function_returns = get_function_signatures_in_folder(folder_path)

UDFS = [func for func in function_signatures
        if not func['udf_name'].startswith(('extract_function_signatures', 'get_function_signatures_in_folder', 'docstring_to_yaml'))]

UDFS_YAML = extract_function_schema_yaml_in_folder(folder_path)
