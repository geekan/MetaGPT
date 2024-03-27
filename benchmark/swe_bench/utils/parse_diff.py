import re
from typing import Dict, List

from benchmark.swe_bench.utils.enums import FileChangeMode, LineChangeType
from metagpt.logs import logger


def extract_changes_from_patch(diff: str) -> List[Dict[str, any]]:
    """Parses the patch text through the standard syntax of git diff, outputs the information of added and deleted lines.

    Extracts detailed information about file changes based on the output content of git diff.

    Args:
        diff: A string containing the output of git diff.

    Returns:
        A list of dictionaries containing information about each file change.
    """
    changes = []
    current_file = None

    file_pattern = re.compile(r"^diff --git a/(.+) b/(.+)$")
    line_change_pattern = re.compile(r"^@@ -(\d+),\d+ \+(\d+),\d+ @@.*$")
    new_file_flag_line = "--- /dev/null"
    deleted_file_flag_line = "+++ /dev/null"

    for line in diff.splitlines():
        file_section_start = file_pattern.match(line)
        if file_section_start:
            if current_file:
                changes.append(current_file)
            file_a, file_b = file_section_start.groups()
            current_file = start_new_file_section(file_a, file_b)
            current_file["mode"] = FileChangeMode.change
        elif current_file:
            # 匹配到新文件模式，标记当前文件为新增
            if line == new_file_flag_line:
                current_file["mode"] = FileChangeMode.create
            # 匹配到删除文件模式，标记当前文件为删除
            elif line == deleted_file_flag_line:
                current_file["mode"] = FileChangeMode.delete
            update_file_changes(current_file, line, line_change_pattern)

    if current_file:
        changes.append(current_file)

    return changes


def start_new_file_section(file_before_change: str, file_after_change: str) -> Dict[str, any]:
    """Function to initialize a new file section

    When encountering a new file change, this function is called to initialize a dictionary recording the file change information.

    Args:
        file_before_change: The file name before the change
        file_after_change: The file name after the change, or "/dev/null" if the file was deleted.

    Returns:
        A dictionary representing the file change.
    """
    return {
        "file_before_change": file_before_change,
        "file_after_change": file_after_change,
        "changes": [],
    }


def update_file_changes(current_file: Dict[str, any], line: str, line_change_pattern: re.Pattern):
    """Updates the current file change information

    Updates the current file's change record based on a line from the diff.

    Args:
        current_file: The current file information being processed
        line: The current line from the diff
        line_change_pattern: The regex pattern used to identify line changes
    """
    line_change_match = line_change_pattern.match(line)
    if line_change_match:
        current_file["base_line"], current_file["changed_line"] = map(int, line_change_match.groups())
    elif line.startswith("+"):
        current_file["changes"].append(
            {"type": LineChangeType.addition, "line": current_file.get("changed_line", 1), "content": line[1:]}
        )
        current_file["changed_line"] = current_file.get("changed_line", 0) + 1
    elif line.startswith("-"):
        current_file["changes"].append(
            {"type": LineChangeType.deletion, "line": current_file.get("base_line", 1), "content": line[1:]}
        )
        current_file["base_line"] = current_file.get("base_line", 0) + 1


def filter_changed_line(patch):
    """Filters changed lines

    Filters the part of the change record of the current file that needs to be used.

    Args:
        patch: The git diff text
    """
    parsed_changes = extract_changes_from_patch(patch)
    res = {}
    for change in parsed_changes:
        file_name = change["file_before_change"]
        res[file_name] = []
        # 新增的文件略过
        if change["mode"] is FileChangeMode.create:
            continue
        for c in change["changes"]:
            if c["type"] is LineChangeType.addition:
                continue
            logger.debug(f"  {c['type']} at line {c['line']}: {c['content']}")
            res[file_name].append(c)
    return res
