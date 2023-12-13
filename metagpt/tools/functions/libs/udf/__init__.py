import ast
import os
import inspect
import importlib
from pathlib import Path
from typing import Dict, List


def extract_function_signatures(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        source_code = file.read()

    tree = ast.parse(source_code)
    function_signatures = []
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

    return function_signatures


def get_function_signatures_in_folder(folder_path):
    python_files = [f for f in os.listdir(folder_path) if f.endswith('.py')]
    all_function_signatures = []

    for file_name in python_files:
        file_path = os.path.join(folder_path, file_name)
        function_signatures = extract_function_signatures(file_path)
        all_function_signatures.extend(function_signatures)

    return all_function_signatures


folder_path = str(Path(__file__).parent.absolute())
function_signatures = get_function_signatures_in_folder(folder_path)

UDFS = [func for func in function_signatures
        if not func['udf_name'].startswith(('extract_function_signatures', 'get_function_signatures_in_folder'))]


# TODO: Create Yaml style UDFS Schema
def udfs2yaml(udfs: List[Dict]) -> Dict:
    pass
