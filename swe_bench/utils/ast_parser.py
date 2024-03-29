import ast
from pathlib import Path


class ASTParser(ast.NodeVisitor):
    def __init__(self, file_name, code_path, valid_line_set):
        self.node_parents = {}  # 节点到父节点的映射
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
            # 获取从开始行号到结束行号的所有行内容
            import_statement_lines = self.source_code.splitlines()[node.lineno - 1 : node.end_lineno]
            complete_statement = "".join([line.strip() for line in import_statement_lines])
        else:  # 在Python 3.8之前的版本中，没有end_lineno
            # 只能获取开始的行
            complete_statement = self.source_code.splitlines()[node.lineno - 1].strip()
        # import 节点没有 name，这里将完整的语句作为节点名称
        setattr(node, "name", complete_statement)
        return self.get_node_full_name(node)

    def traverse(self, node, parent_node=None):
        if parent_node and not isinstance(parent_node, ast.Module):
            self.node_parents[node] = parent_node

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node_full_name = self.get_node_full_name(node)
            if parent_node and isinstance(parent_node, ast.ClassDef):
                self.symbol_changes["method"].append(node_full_name)
                self.symbol_changes["class"].append(self.get_node_full_name(parent_node))
            else:
                self.symbol_changes["function"].append(node_full_name)

        elif isinstance(node, ast.ImportFrom):
            node_full_name = self.get_node_full_name_by_import(node)
            self.symbol_changes["import"].append(node_full_name)

        elif isinstance(node, ast.Global):
            node_full_name = self.get_node_full_name_by_import(node)
            self.symbol_changes["global"].append(node_full_name)

        # 遍历当前节点的所有子节点
        for child in ast.iter_child_nodes(node):
            self.traverse(node=child, parent_node=node)
