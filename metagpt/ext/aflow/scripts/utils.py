"""
@Time    : 2024/7/24 16:37
@Author  : didi
@File    : utils.py
@Acknowledgement https://github.com/evalplus/evalplus/blob/master/evalplus/sanitize.py
"""

import ast
import json
import re
import traceback
from enum import Enum
from typing import Any, Dict, Generator, List, Optional, Set, Tuple

import tree_sitter_python
from tree_sitter import Language, Node, Parser


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


class NodeType(Enum):
    CLASS = "class_definition"
    FUNCTION = "function_definition"
    IMPORT = ["import_statement", "import_from_statement"]
    IDENTIFIER = "identifier"
    ATTRIBUTE = "attribute"
    RETURN = "return_statement"
    EXPRESSION = "expression_statement"
    ASSIGNMENT = "assignment"


def traverse_tree(node: Node) -> Generator[Node, None, None]:
    """
    Traverse the tree structure starting from the given node.

    :param node: The root node to start the traversal from.
    :return: A generator object that yields nodes in the tree.
    """
    cursor = node.walk()
    depth = 0

    visited_children = False
    while True:
        if not visited_children:
            yield cursor.node
            if not cursor.goto_first_child():
                depth += 1
                visited_children = True
        elif cursor.goto_next_sibling():
            visited_children = False
        elif not cursor.goto_parent() or depth == 0:
            break
        else:
            depth -= 1


def syntax_check(code, verbose=False):
    try:
        ast.parse(code)
        return True
    except (SyntaxError, MemoryError):
        if verbose:
            traceback.print_exc()
        return False


def code_extract(text: str) -> str:
    lines = text.split("\n")
    longest_line_pair = (0, 0)
    longest_so_far = 0

    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            current_lines = "\n".join(lines[i : j + 1])
            if syntax_check(current_lines):
                current_length = sum(1 for line in lines[i : j + 1] if line.strip())
                if current_length > longest_so_far:
                    longest_so_far = current_length
                    longest_line_pair = (i, j)

    return "\n".join(lines[longest_line_pair[0] : longest_line_pair[1] + 1])


def get_definition_name(node: Node) -> str:
    for child in node.children:
        if child.type == NodeType.IDENTIFIER.value:
            return child.text.decode("utf8")


def has_return_statement(node: Node) -> bool:
    traverse_nodes = traverse_tree(node)
    for node in traverse_nodes:
        if node.type == NodeType.RETURN.value:
            return True
    return False


def get_deps(nodes: List[Tuple[str, Node]]) -> Dict[str, Set[str]]:
    def dfs_get_deps(node: Node, deps: Set[str]) -> None:
        for child in node.children:
            if child.type == NodeType.IDENTIFIER.value:
                deps.add(child.text.decode("utf8"))
            else:
                dfs_get_deps(child, deps)

    name2deps = {}
    for name, node in nodes:
        deps = set()
        dfs_get_deps(node, deps)
        name2deps[name] = deps
    return name2deps


def get_function_dependency(entrypoint: str, call_graph: Dict[str, str]) -> Set[str]:
    queue = [entrypoint]
    visited = {entrypoint}
    while queue:
        current = queue.pop(0)
        if current not in call_graph:
            continue
        for neighbour in call_graph[current]:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)
    return visited


def sanitize(code: str, entrypoint: Optional[str] = None) -> str:
    """
    Sanitize and extract relevant parts of the given Python code.
    This function parses the input code, extracts import statements, class and function definitions,
    and variable assignments. If an entrypoint is provided, it only includes definitions that are
    reachable from the entrypoint in the call graph.

    :param code: The input Python code as a string.
    :param entrypoint: Optional name of a function to use as the entrypoint for dependency analysis.
    :return: A sanitized version of the input code, containing only relevant parts.
    """
    code = code_extract(code)
    code_bytes = bytes(code, "utf8")
    parser = Parser(Language(tree_sitter_python.language()))
    tree = parser.parse(code_bytes)
    class_names = set()
    function_names = set()
    variable_names = set()

    root_node = tree.root_node
    import_nodes = []
    definition_nodes = []

    for child in root_node.children:
        if child.type in NodeType.IMPORT.value:
            import_nodes.append(child)
        elif child.type == NodeType.CLASS.value:
            name = get_definition_name(child)
            if not (name in class_names or name in variable_names or name in function_names):
                definition_nodes.append((name, child))
                class_names.add(name)
        elif child.type == NodeType.FUNCTION.value:
            name = get_definition_name(child)
            if not (name in function_names or name in variable_names or name in class_names) and has_return_statement(
                child
            ):
                definition_nodes.append((name, child))
                function_names.add(get_definition_name(child))
        elif child.type == NodeType.EXPRESSION.value and child.children[0].type == NodeType.ASSIGNMENT.value:
            subchild = child.children[0]
            name = get_definition_name(subchild)
            if not (name in variable_names or name in function_names or name in class_names):
                definition_nodes.append((name, subchild))
                variable_names.add(name)

    if entrypoint:
        name2deps = get_deps(definition_nodes)
        reacheable = get_function_dependency(entrypoint, name2deps)

    sanitized_output = b""

    for node in import_nodes:
        sanitized_output += code_bytes[node.start_byte : node.end_byte] + b"\n"

    for pair in definition_nodes:
        name, node = pair
        if entrypoint and name not in reacheable:
            continue
        sanitized_output += code_bytes[node.start_byte : node.end_byte] + b"\n"
    return sanitized_output[:-1].decode("utf8")
