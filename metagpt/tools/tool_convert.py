import inspect

from metagpt.utils.parse_docstring import GoogleDocstringParser, remove_spaces


def convert_code_to_tool_schema(obj, include: list[str] = []):
    docstring = inspect.getdoc(obj)
    assert docstring, "no docstring found for the objects, skip registering"

    if inspect.isclass(obj):
        schema = {"type": "class", "description": remove_spaces(docstring), "methods": {}}
        for name, method in inspect.getmembers(obj, inspect.isfunction):
            if include and name not in include:
                continue
            # method_doc = inspect.getdoc(method)
            method_doc = get_class_method_docstring(obj, name)
            if method_doc:
                schema["methods"][name] = function_docstring_to_schema(method, method_doc)

    elif inspect.isfunction(obj):
        schema = function_docstring_to_schema(obj, docstring)

    return schema


def function_docstring_to_schema(fn_obj, docstring):
    function_type = "function" if not inspect.iscoroutinefunction(fn_obj) else "async_function"
    return {"type": function_type, **docstring_to_schema(docstring)}


def docstring_to_schema(docstring: str):
    if docstring is None:
        return {}

    parser = GoogleDocstringParser(docstring=docstring)

    # 匹配简介部分
    description = parser.parse_desc()

    # 匹配Args部分
    params = parser.parse_params()
    parameter_schema = {"properties": {}, "required": []}
    for param in params:
        param_name, param_type, param_desc = param
        # check required or optional
        is_optional, param_type = parser.check_and_parse_optional(param_type)
        if not is_optional:
            parameter_schema["required"].append(param_name)
        # type and desc
        param_dict = {"type": param_type, "description": remove_spaces(param_desc)}
        # match Default for optional args
        has_default_val, default_val = parser.check_and_parse_default_value(param_desc)
        if has_default_val:
            param_dict["default"] = default_val
        # match Enum
        has_enum, enum_vals = parser.check_and_parse_enum(param_desc)
        if has_enum:
            param_dict["enum"] = enum_vals
        # add to parameter schema
        parameter_schema["properties"].update({param_name: param_dict})

    # 匹配Returns部分
    returns = parser.parse_returns()

    # 构建YAML字典
    schema = {
        "description": description,
        "parameters": parameter_schema,
    }
    if returns:
        schema["returns"] = [{"type": ret[0], "description": remove_spaces(ret[1])} for ret in returns]

    return schema


def get_class_method_docstring(cls, method_name):
    """Retrieve a method's docstring, searching the class hierarchy if necessary."""
    for base_class in cls.__mro__:
        if method_name in base_class.__dict__:
            method = base_class.__dict__[method_name]
            if method.__doc__:
                return method.__doc__
    return None  # No docstring found in the class hierarchy
