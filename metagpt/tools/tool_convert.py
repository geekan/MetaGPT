import ast
import inspect

from metagpt.utils.parse_docstring import GoogleDocstringParser, remove_spaces

PARSER = GoogleDocstringParser


def convert_code_to_tool_schema(obj, include: list[str] = None) -> dict:
    """Converts an object (function or class) to a tool schema by inspecting the object"""
    docstring = inspect.getdoc(obj)
    # assert docstring, "no docstring found for the objects, skip registering"

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


def convert_code_to_tool_schema_ast(code: str) -> list[dict]:
    """Converts a code string to a list of tool schemas by parsing the code with AST"""

    visitor = CodeVisitor(code)
    parsed_code = ast.parse(code)
    visitor.visit(parsed_code)

    return visitor.get_tool_schemas()


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


class CodeVisitor(ast.NodeVisitor):
    """Visit and convert the AST nodes within a code file to tool schemas"""

    def __init__(self, source_code: str):
        self.tool_schemas = {}  # {tool_name: tool_schema}
        self.source_code = source_code

    def visit_ClassDef(self, node):
        class_schemas = {"type": "class", "description": remove_spaces(ast.get_docstring(node)), "methods": {}}
        for body_node in node.body:
            if isinstance(body_node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                not body_node.name.startswith("_") or body_node.name == "__init__"
            ):
                func_schemas = self._get_function_schemas(body_node)
                class_schemas["methods"].update({body_node.name: func_schemas})
        class_schemas["code"] = ast.get_source_segment(self.source_code, node)
        self.tool_schemas[node.name] = class_schemas

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node)

    def _visit_function(self, node):
        if node.name.startswith("_"):
            return
        function_schemas = self._get_function_schemas(node)
        function_schemas["code"] = ast.get_source_segment(self.source_code, node)
        self.tool_schemas[node.name] = function_schemas

    def _get_function_schemas(self, node):
        docstring = remove_spaces(ast.get_docstring(node))
        overall_desc, param_desc = PARSER.parse(docstring)
        return {
            "type": "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
            "description": overall_desc,
            "signature": self._get_function_signature(node),
            "parameters": param_desc,
        }

    def _get_function_signature(self, node):
        args = []
        defaults = dict(zip([arg.arg for arg in node.args.args][-len(node.args.defaults) :], node.args.defaults))
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                annotation = ast.unparse(arg.annotation)
                arg_str += f": {annotation}"
            if arg.arg in defaults:
                default_value = ast.unparse(defaults[arg.arg])
                arg_str += f" = {default_value}"
            args.append(arg_str)

        return_annotation = ""
        if node.returns:
            return_annotation = f" -> {ast.unparse(node.returns)}"

        return f"({', '.join(args)}){return_annotation}"

    def get_tool_schemas(self):
        return self.tool_schemas
