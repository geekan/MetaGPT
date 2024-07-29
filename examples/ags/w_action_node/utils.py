# -*- coding: utf-8 -*-
# @Date    : 7/2/2024 17:36 PM
# @Author  : didi
# @Desc    : utils for experiment

import json
import re
from typing import List, Dict, Any, Tuple
from metagpt.llm import LLM
from metagpt.actions.action_node import ActionNode
from examples.ags.w_action_node.operator_an import TestCaseExtractOp
from examples.ags.w_action_node.prompt import EXTRACT_CASE_PROMPT

def extract_task_id(task_id: str) -> int:
    """Extract the numeric part of the task_id."""
    match = re.search(r'/(\d+)', task_id)
    return int(match.group(1)) if match else 0

def jsonl_ranker(input_file: str, output_file: str):
    """
    Read a JSONL file, sort the entries based on task_id, and write to a new JSONL file.
    
    :param input_file: Path to the input JSONL file
    :param output_file: Path to the output JSONL file
    """
    # Read and parse the JSONL file
    with open(input_file, 'r') as f:
        data = [json.loads(line) for line in f]
    
    # Sort the data based on the numeric part of task_id
    sorted_data = sorted(data, key=lambda x: extract_task_id(x['task_id']))
    
    # Write the sorted data to a new JSONL file
    with open(output_file, 'w') as f:
        for item in sorted_data:
            f.write(json.dumps(item) + '\n')

# def extract_test_cases_from_jsonl(problem_id:str, file_path:str="public_test.jsonl"):
#     # TODO 这个JSONL效率有点神经病
#     if problem_id == "Humaneval/87":
#         return [ ["get_row", [[[1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 1, 6], [1, 2, 3, 4, 5, 1]], 1], [(0, 0), (1, 4), (1, 0), (2, 5), (2, 0)]], ["get_row", [[], 1], []], ["get_row", [[[], [1], [1, 2, 3]], 3], [(2, 2)]] ]
#     elif problem_id == "Humaneval/95":
#         return [ ["check_dict_case", [{"a": "apple", "b": "banana"}], True], ["check_dict_case", [{"a": "apple", "A": "banana", "B": "banana"}], False], ["check_dict_case", [{"a": "apple", "8": "banana", "a": "apple"}], False], ["check_dict_case", [{"Name": "John", "Age": "36", "City": "Houston"}], False], ["check_dict_case", [{"STATE": "NC", "ZIP": "12345"}], True] ]
#     elif problem_id == "Humaneval/107":
#         return [ ["even_odd_palindrome", [3], (1, 2)], ["even_odd_palindrome", [12], (4, 6)] ]
#     elif problem_id == "Humaneval/112":
#         return [ ["reverse_delete", ["abcde", "ae"], ("bcd", False)], ["reverse_delete", ["abcdef", "b"], ("acdef", False)], ["reverse_delete", ["abcdedcba", "ab"], ("cdedc", True)] ]
#     elif problem_id == "Humaneval/127":
#         return [ ["intersection", [(1, 2), (2, 3)], "NO"], ["intersection", [(-1, 1), (0, 4)], "NO"], ["intersection", [(-3, -1), (-5, 5)], "YES"] ]
#     elif problem_id == "Humaneval/136":
#         return [ ["largest_smallest_integers", [2, 4, 1, 3, 5, 7], (None, 1)], ["largest_smallest_integers", [], (None, None)], ["largest_smallest_integers", [0], (None, None)] ]
#     elif problem_id == "Humaneval/148":
#         return [ ["bf", ["Jupiter", "Neptune"], ("Saturn", "Uranus")], ["bf", ["Earth", "Mercury"], ("Venus",)], ["bf", ["Mercury", "Uranus"], ("Venus", "Earth", "Mars", "Jupiter", "Saturn")], ["bf", ["InvalidPlanet", "Neptune"], ()], ["bf", ["Jupiter", "InvalidPlanet"], ()], ["bf", ["Mercury", "Mercury"], ()] ]
#     elif problem_id == "Humaneval/155":
#         return [ ["even_odd_count", [-12], (1, 1)], ["even_odd_count", [123], (1, 2)] ]

#     with open(file_path, 'r') as file:
#         for line in file:
#             data = json.loads(line)
#             if problem_id in data:
#                 return data[problem_id]
    
#     return None

import json
import ast

def parse_python_literal(s):
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return s

def extract_test_cases_from_jsonl(problem_id:str, file_path:str="public_test_reflexion.jsonl"):
    # 保留原有的硬编码测试用例
    hardcoded_cases = {
        "HumanEval/32": "",
        "HumanEval/38": "",
        "HumanEval/50": "",
    }

    # 检查是否有硬编码的测试用例
    if problem_id in hardcoded_cases:
        return hardcoded_cases[problem_id]

    # 如果没有硬编码的测试用例，从文件中读取
    with open(file_path, 'r') as file:
        for line in file:
            data = json.loads(line)
            if data.get("id") == problem_id:
                return data.get("test")

    return None  # 如果没有找到问题，返回 None

def extract_test_cases(docstring: str) -> List[Tuple[str, List[Any], Any]]:
    # 使用正则表达式匹配测试用例，现在捕获函数名和任意输出
    pattern = r'>>> (\w+)\((.*?)\)\n\s*(.*?)(?=\n|$)'
    matches = re.findall(pattern, docstring, re.DOTALL)
    
    test_cases = []
    for match in matches:
        func_name, input_str, expected_output = match
        
        # 处理输入
        input_list = []
        for item in input_str.split(','):
            item = item.strip()
            try:
                # 尝试将输入转换为数值类型
                if '.' in item:
                    input_list.append(float(item))
                else:
                    input_list.append(int(item))
            except ValueError:
                # 如果无法转换为数值，则保留为字符串
                input_list.append(item.strip("'\""))
        
        # 处理输出
        try:
            # 尝试将输出转换为数值或布尔值
            if expected_output.lower() == 'true':
                expected_output = True
            elif expected_output.lower() == 'false':
                expected_output = False
            elif '.' in expected_output:
                expected_output = float(expected_output)
            else:
                expected_output = int(expected_output)
        except ValueError:
            # 如果无法转换，则保留为字符串
            expected_output = expected_output.strip("'\"")
        
        test_cases.append([func_name, input_list, expected_output])
    
    return test_cases


async def llm_extract_test_case(id, problem_description: str, file_path:str="public_test.jsonl"):
    prompt = EXTRACT_CASE_PROMPT.format(problem_description=problem_description)
    node = await ActionNode.from_pydantic(TestCaseExtractOp).fill(context=prompt, llm=LLM())
    result = node.instruct_content.model_dump()
    with open(file_path,"a") as f:
        f.write(json.dumps({id:result["test_cases"]}) + '\n')
    return {id:result["test_cases"]}

import json

# def test_cases_2_test_functions(solution: str, test_case: List):
#     print("test_case", test_case)
#     function_name = test_case[0]
    
#     def format_param(param):
#         if isinstance(param, str):
#             return repr(param)
#         elif isinstance(param, (int, float, bool)):
#             return str(param)
#         elif isinstance(param, list):
#             return '[' + ', '.join(format_param(item) for item in param) + ']'
#         elif isinstance(param, tuple):
#             return '(' + ', '.join(format_param(item) for item in param) + ')'
#         elif isinstance(param, dict):
#             return '{' + ', '.join(f'{format_param(k)}: {format_param(v)}' for k, v in param.items()) + '}'
#         elif isinstance(param, type(None)):
#             return 'None'
#         else:
#             raise ValueError(f"Unsupported parameter type: {type(param)}")

#     parameters = ', '.join(format_param(item) for item in test_case[1])
#     print(test_case[1], parameters)

#     expected_output = format_param(test_case[2])
#     print(type(test_case[2]), test_case[2], expected_output)
    
#     tester_function = f"""
# {solution}

# def check(candidate):
#     assert candidate({parameters}) == {expected_output}

# check({function_name})
#     """
    
#     print(f"""
#     Generated test function:
#     {tester_function}
#     """)
    
#     return tester_function
    

def test_cases_2_test_functions(solution: str, test_cases: str):
    tester_function = f"""
{solution}

{test_cases}
""" 
    return tester_function