import re


def extract_scripts_from_codetext(codetext: str):
    script_names = []
    # 提供的文本内容，可能包含多个 [start of ... .py]
    """
    [end of README.rst]
    [start of sklearn/compose/_target.py]
    ... 文件内容 ...
    [end of sklearn/compose/_target.py]
    [start of another_module/example.py]
    ... 文件内容 ...
    [end of another_module/example.py]
    """

    # 使用正则表达式匹配所有 “[start of 任意字符.py]”
    matches = re.findall(r"\[start of ([^\]]+\.py)\]", codetext)

    if matches:
        # 遍历所有匹配的文件名并打印
        for script_name in matches:
            print("Extracted script name:", script_name)
            script_names.append(script_name)
    else:
        print("No script names found in the text.")
    return script_names
