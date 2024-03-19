import re


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
