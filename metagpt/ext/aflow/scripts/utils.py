# -*- coding: utf-8 -*-
# @Date    : 7/2/2024 17:36 PM
# @Author  : didi
# @Desc    : utils for experiment

import ast
import json
import re
from typing import Any, List, Tuple


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


def extract_test_cases_from_jsonl(entry_point: str, dataset: str = "HumanEval"):
    if dataset == "HumanEval":
        file_path = "metagpt/ext/aflow/data/humaneval_public_test.jsonl"
        # Retain the original hardcoded test cases
        hardcoded_cases = {
            "find_zero": "",
            "decode_cyclic": "",
            "decode_shift": "",
            "by_length": "",
            "add": "",
            "triangle_area": "",
            "correct_bracketing": "",
            "solve": "",
            "sum_squares": "",
            "starts_one_ends": "",
        }
    elif dataset == "MBPP":
        file_path = "metagpt/ext/aflow/data/mbpp_public_test.jsonl"
        hardcoded_cases = {
            "remove_odd": "",
            "replace_spaces": "",
            "snake_to_camel": "",
            "Split": "",
            "swap_List": "",
            "square_Sum": "",
            "sort_sublists": "",
            "unique_sublists": "",
        }
    # Check if there are hardcoded test cases
    if entry_point in hardcoded_cases:
        return hardcoded_cases[entry_point]

    # If there are no hardcoded test cases, read from the file
    with open(file_path, "r") as file:
        for line in file:
            data = json.loads(line)
            if data.get("entry_point") == entry_point:
                return data.get("test")

    return None


def extract_test_cases(docstring: str) -> List[Tuple[str, List[Any], Any]]:
    # Use regular expressions to match test cases, now capturing function names and any output
    pattern = r">>> (\w+)\((.*?)\)\n\s*(.*?)(?=\n|$)"
    matches = re.findall(pattern, docstring, re.DOTALL)

    test_cases = []
    for match in matches:
        func_name, input_str, expected_output = match

        # Process input
        input_list = []
        for item in input_str.split(","):
            item = item.strip()
            try:
                # Try to convert input to numeric type
                if "." in item:
                    input_list.append(float(item))
                else:
                    input_list.append(int(item))
            except ValueError:
                # If unable to convert to numeric, keep as string
                input_list.append(item.strip("'\""))

        # Process output
        try:
            # Try to convert output to numeric or boolean value
            if expected_output.lower() == "true":
                expected_output = True
            elif expected_output.lower() == "false":
                expected_output = False
            elif "." in expected_output:
                expected_output = float(expected_output)
            else:
                expected_output = int(expected_output)
        except ValueError:
            # If unable to convert, keep as string
            expected_output = expected_output.strip("'\"")

        test_cases.append([func_name, input_list, expected_output])

    return test_cases


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
