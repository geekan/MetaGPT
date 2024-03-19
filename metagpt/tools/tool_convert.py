import inspect

from metagpt.utils.parse_docstring import GoogleDocstringParser, remove_spaces

PARSER = GoogleDocstringParser


def convert_code_to_tool_schema(obj, include: list[str] = None):
    docstring = inspect.getdoc(obj)
    assert docstring, "no docstring found for the objects, skip registering"

    if inspect.isclass(obj):
        schema = {"type": "class", "description": remove_spaces(docstring), "methods": {}}
        for name, method in inspect.getmembers(obj, inspect.isfunction):
            if name.startswith("_") and name != "__init__":  # skip private methodss
                continue
            if include and name not in include:
                continue
            # method_doc = inspect.getdoc(method)
            method_doc = get_class_method_docstring(obj, name)
            if method_doc:
                schema["methods"][name] = function_docstring_to_schema(method, method_doc)

    elif inspect.isfunction(obj):
        schema = function_docstring_to_schema(obj, docstring)

    return schema


def function_docstring_to_schema(fn_obj, docstring) -> dict:
    """
    Converts a function's docstring into a schema dictionary.

    Args:
        fn_obj: The function object.
        docstring: The docstring of the function.

    Returns:
        A dictionary representing the schema of the function's docstring.
        The dictionary contains the following keys:
        - 'type': The type of the function ('function' or 'async_function').
        - 'description': The first section of the docstring describing the function overall. Provided to LLMs for both recommending and using the function.
        - 'signature': The signature of the function, which helps LLMs understand how to call the function.
        - 'parameters': Docstring section describing parameters including args and returns, served as extra details for LLM perception.
    """
    signature = inspect.signature(fn_obj)

    docstring = remove_spaces(docstring)

    overall_desc, param_desc = PARSER.parse(docstring)

    function_type = "function" if not inspect.iscoroutinefunction(fn_obj) else "async_function"

    return {"type": function_type, "description": overall_desc, "signature": str(signature), "parameters": param_desc}


def get_class_method_docstring(cls, method_name):
    """Retrieve a method's docstring, searching the class hierarchy if necessary."""
    for base_class in cls.__mro__:
        if method_name in base_class.__dict__:
            method = base_class.__dict__[method_name]
            if method.__doc__:
                return method.__doc__
    return None  # No docstring found in the class hierarchy
