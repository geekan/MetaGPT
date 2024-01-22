import inspect
import re


def remove_spaces(text):
    return re.sub(r"\s+", " ", text)


def convert_code_to_tool_schema(obj, include: list[str] = []):
    docstring = inspect.getdoc(obj)
    assert docstring, "no docstring found for the objects, skip registering"

    if inspect.isclass(obj):
        schema = {"type": "class", "description": remove_spaces(docstring), "methods": {}}
        for name, method in inspect.getmembers(obj, inspect.isfunction):
            if include and name not in include:
                continue
            method_doc = inspect.getdoc(method)
            if method_doc:
                schema["methods"][name] = docstring_to_schema(method_doc)

    elif inspect.isfunction(obj):
        schema = {
            "type": "function",
            **docstring_to_schema(docstring),
        }

    schema = {obj.__name__: schema}

    return schema


def docstring_to_schema(docstring: str):
    if docstring is None:
        return {}

    # 匹配简介部分
    description_match = re.search(r"^(.*?)(?:Args:|Returns:|Raises:|$)", docstring, re.DOTALL)
    description = remove_spaces(description_match.group(1)) if description_match else ""

    # 匹配Args部分
    args_match = re.search(r"Args:\s*(.*?)(?:Returns:|Raises:|$)", docstring, re.DOTALL)
    _args = args_match.group(1).strip() if args_match else ""
    # variable_pattern = re.compile(r"(\w+)\s*\((.*?)\):\s*(.*)")
    variable_pattern = re.compile(
        r"(\w+)\s*\((.*?)\):\s*(.*?)(?=\n\s*\w+\s*\(|\Z)", re.DOTALL
    )  # (?=\n\w+\s*\(|\Z) is to assert that what follows is either the start of the next parameter (indicated by a newline, some word characters, and an opening parenthesis) or the end of the string (\Z).

    params = variable_pattern.findall(_args)
    parameter_schema = {"properties": {}, "required": []}
    for param in params:
        param_name, param_type, param_desc = param
        # check required or optional
        if "optional" in param_type:
            param_type = param_type.replace(", optional", "")
        else:
            parameter_schema["required"].append(param_name)
        # type and desc
        param_dict = {"type": param_type, "description": remove_spaces(param_desc)}
        # match Default for optional args
        default_val = re.search(r"Defaults to (.+?)\.", param_desc)
        if default_val:
            param_dict["default"] = default_val.group(1)
        # match Enum
        enum_val = re.search(r"Enum: \[(.+?)\]", param_desc)
        if enum_val:
            param_dict["enum"] = [e.strip() for e in enum_val.group(1).split(",")]
        # add to parameter schema
        parameter_schema["properties"].update({param_name: param_dict})

    # 匹配Returns部分
    returns_match = re.search(r"Returns:\s*(.*?)(?:Raises:|$)", docstring, re.DOTALL)
    returns = returns_match.group(1).strip() if returns_match else ""
    return_pattern = re.compile(r"^(.*)\s*:\s*(.*)$")
    returns = return_pattern.findall(returns)

    # 构建YAML字典
    schema = {
        "description": description,
        "parameters": parameter_schema,
    }
    if returns:
        schema["returns"] = [{"type": ret[0], "description": remove_spaces(ret[1])} for ret in returns]

    return schema
