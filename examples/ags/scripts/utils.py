# -*- coding: utf-8 -*-
# @Date    : 7/2/2024 17:36 PM
# @Author  : didi
# @Desc    : utils for experiment

import ast
import json
import re
from typing import Any, List, Tuple

from examples.ags.scripts.operator_an import TestCaseExtractOp
from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM


def extract_task_id(task_id: str) -> int:
    """Extract the numeric part of the task_id."""
    match = re.search(r"/(\d+)", task_id)
    return int(match.group(1)) if match else 0


def get_hotpotqa(path: str):
    # Parses each jsonl line and yields it as a dictionary
    def parse_jsonl(path):
        with open(path) as f:
            for line in f:
                yield json.loads(line)

    datas = list(parse_jsonl(path))
    return {data["_id"]: data for data in datas}


def sort_json_by_key(input_file: str, output_file: str, key: str = "task_id"):
    """
    Read a JSONL file, sort the entries based on task_id, and write to a new JSONL file.

    :param input_file: Path to the input JSONL file
    :param output_file: Path to the output JSONL file
    """
    # Read and parse the JSONL file
    with open(input_file, "r") as f:
        data = [json.loads(line) for line in f]

    # Sort the data based on the numeric part of task_id
    sorted_data = sorted(data, key=lambda x: extract_task_id(x[key]))

    # Write the sorted data to a new JSONL file
    with open(output_file, "w") as f:
        for item in sorted_data:
            f.write(json.dumps(item) + "\n")


def parse_python_literal(s):
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return s


def extract_test_cases_from_jsonl(
    problem_id: str, file_path: str = "examples/ags/benchmark/data/humaneval_public_test.jsonl"
):
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
    with open(file_path, "r") as file:
        for line in file:
            data = json.loads(line)
            if data.get("task_id") == problem_id:
                return data.get("test")

    return None  # 如果没有找到问题，返回 None


def extract_test_cases(docstring: str) -> List[Tuple[str, List[Any], Any]]:
    # 使用正则表达式匹配测试用例，现在捕获函数名和任意输出
    pattern = r">>> (\w+)\((.*?)\)\n\s*(.*?)(?=\n|$)"
    matches = re.findall(pattern, docstring, re.DOTALL)

    test_cases = []
    for match in matches:
        func_name, input_str, expected_output = match

        # 处理输入
        input_list = []
        for item in input_str.split(","):
            item = item.strip()
            try:
                # 尝试将输入转换为数值类型
                if "." in item:
                    input_list.append(float(item))
                else:
                    input_list.append(int(item))
            except ValueError:
                # 如果无法转换为数值，则保留为字符串
                input_list.append(item.strip("'\""))

        # 处理输出
        try:
            # 尝试将输出转换为数值或布尔值
            if expected_output.lower() == "true":
                expected_output = True
            elif expected_output.lower() == "false":
                expected_output = False
            elif "." in expected_output:
                expected_output = float(expected_output)
            else:
                expected_output = int(expected_output)
        except ValueError:
            # 如果无法转换，则保留为字符串
            expected_output = expected_output.strip("'\"")

        test_cases.append([func_name, input_list, expected_output])

    return test_cases


# async def llm_extract_test_case(id, problem_description: str, file_path: str = "public_test.jsonl"):
#     prompt = EXTRACT_CASE_PROMPT.format(problem_description=problem_description)
#     node = await ActionNode.from_pydantic(TestCaseExtractOp).fill(context=prompt, llm=LLM())
#     result = node.instruct_content.model_dump()
#     with open(file_path, "a") as f:
#         f.write(json.dumps({id: result["test_cases"]}) + "\n")
#     return {id: result["test_cases"]}


def test_cases_2_test_functions(solution: str, test_cases: str):
    tester_function = f"""
{solution}

{test_cases}
"""
    return tester_function


def test_case_2_test_function(solution: str, test_case: str, entry_point: str):
    tester_function = f"""
{solution}


def check(candidate):
    {test_case}

def test_check():
    check({entry_point})

test_check()
"""
    return tester_function
