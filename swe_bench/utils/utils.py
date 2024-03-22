import json
import os
import re

from metagpt.logs import logger


def check_existing_ids(output_file):
    existing_ids = set()
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            for line in f:
                data = json.loads(line)
                instance_id = data["instance_id"]
                existing_ids.add(instance_id)
    logger.info(f"Read {len(existing_ids)} already completed ids from {output_file}")
    return existing_ids


def extract_diff(response):
    """
    Extracts the diff from a response formatted in different ways
    """
    if response is None:
        return None
    diff_matches = []
    other_matches = []
    pattern = re.compile(r"\<([\w-]+)\>(.*?)\<\/\1\>", re.DOTALL)
    for code, match in pattern.findall(response):
        if code in {"diff", "patch"}:
            diff_matches.append(match)
        else:
            other_matches.append(match)
    pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)
    for code, match in pattern.findall(response):
        if code in {"diff", "patch"}:
            diff_matches.append(match)
        else:
            other_matches.append(match)
    if diff_matches:
        return diff_matches[0]
    if other_matches:
        return other_matches[0]
    return response.split("</s>")[0]


def extract_scripts_from_codetext(codetext: str):
    """
    Extracts Python script file names from a given text that contains multiple sections.
    Each section starts with '[start of <script_name>.py]' and ends with '[end of <script_name>.py]'.

    Parameters:
    - codetext (str): A string that may contain multiple sections, each indicating the start of a Python script file.

    Returns:
    - list: A list of extracted Python script file names.

    Example of codetext:
    '''
    [end of README.rst]
    [start of sklearn/compose/_target.py]
    ... file content ...
    [end of sklearn/compose/_target.py]
    [start of another_module/example.py]
    ... file content ...
    [end of another_module/example.py]
    '''
    """
    script_names = []

    # Match all occurrences of '[start of <script_name>.py]'
    matches = re.findall(r"\[start of ([^\]]+\.py)\]", codetext)

    if matches:
        for script_name in matches:
            print("Extracted script name:", script_name)
            script_names.append(script_name)
    else:
        print("No script names found in the text.")

    return script_names
