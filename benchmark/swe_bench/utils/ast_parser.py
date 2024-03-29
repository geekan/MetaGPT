import ast
from pathlib import Path


class ASTParser(ast.NodeVisitor):
    def __init__(self, file_name, code_path, valid_line_set):
        self.node_parents = {}  # Mapping of nodes to their parents
        self.file_name = file_name.replace(".py", "")
        self.symbol_changes = {
            "file": [self.file_name],
            "class": [],
            "function": [],
            "import": [],
            "global": [],
            "method": [],
        }

        self.source_code = Path.read_text(code_path, encoding="utf-8")
        self.tree = ast.parse(self.source_code)
        self.valid_line_set = valid_line_set

    def get_node_full_name(self, node):
        current = node
        node_full_name = current.name
        while current:
            current = self.node_parents.get(current, None)
            if isinstance(current, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                node_full_name = current.name + "." + node_full_name
        return self.file_name + "." + node_full_name

    def get_node_full_name_by_import(self, node):
        if hasattr(node, "end_lineno"):  # Python 3.8+
            # Gets the contents of all lines from the beginning to the end of the line number.
            import_statement_lines = self.source_code.splitlines()[node.lineno - 1 : node.end_lineno]
            complete_statement = "".join([line.strip() for line in import_statement_lines])
        else:  # In versions of Python prior to 3.8, there is no end_lineno
            # Only the beginning row can be fetched
            complete_statement = self.source_code.splitlines()[node.lineno - 1].strip()
        # The import node does not have a name, so the full statement is used here as the node name.
        setattr(node, "name", complete_statement)
        return self.get_node_full_name(node)

    # Traverse the AST and collect the symbol changes
    def traverse(self, node, parent_node=None):
        if parent_node and not isinstance(parent_node, ast.Module):
            self.node_parents[node] = parent_node

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node_full_name = self.get_node_full_name(node)
            # If the parent node is a class, add the method and class to the symbol_changes
            if parent_node and isinstance(parent_node, ast.ClassDef):
                self.symbol_changes["method"].append(node_full_name)
                self.symbol_changes["class"].append(self.get_node_full_name(parent_node))
            # If there is no parent node, add the function to the symbol_changes
            else:
                self.symbol_changes["function"].append(node_full_name)

        elif isinstance(node, ast.ImportFrom):
            node_full_name = self.get_node_full_name_by_import(node)
            self.symbol_changes["import"].append(node_full_name)

        elif isinstance(node, ast.Global):
            node_full_name = self.get_node_full_name_by_import(node)
            self.symbol_changes["global"].append(node_full_name)

        # Iterate over all children of the current node
        for child in ast.iter_child_nodes(node):
            self.traverse(node=child, parent_node=node)
