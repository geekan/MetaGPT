from typing import List, Optional
from abc import ABC, abstractmethod
import os

class CodeNode(ABC):
    def __init__(self,
                 code: str,
                 id: int | str,
                 file_path: str,
                 dataset: str,
                 score: Optional[float] = 0,
                 meta: Optional[dict] = {},
                 parent: Optional['CodeNode'] = None,
                 modification_info: str = None):
        """
        这里有一个空间问题，每个Node都存储code，同时也要保存code到文件file_path;
        TODO：可以考虑code字段只在常用的Node上载入。
        """
        self.code = code
        self.id = id
        self.score = score    # 评估分数
        self.parent = parent  # 父节点
        self.meta = meta # 扩展元数据（如SELA的insights、ADAS的fitness）
        self.children: List['CodeNode'] = []
        self.visit_count = 0
        self.file_path: str = file_path
        self.dataset: str = dataset
        self.modification_info = modification_info

        self.add_to_parent(parent)

        self.write_file()

    def add_child(self, node):
        self.children.append(node)
        node.parent = self

    def add_to_parent(self, parent_node):
        if parent_node:
            parent_node.children.append(self)
            self.parent = parent_node

    @abstractmethod
    def write_file(self):
        pass

    @abstractmethod
    def get_executor(self, llm_config):
        pass


class TreeMemory(ABC):
    def __init__(self, init_code, init_meta, dataset: str, root_path: str, node_class):
        self.node_list = []
        self.dataset = dataset
        self.root_path = root_path
        os.makedirs(self.root_path, exist_ok=True)

        self._init_root_node(init_code, init_meta, node_class)

    @abstractmethod
    def _get_id(self, parent_node: CodeNode = None) -> int | str:
        pass

    @abstractmethod
    def _get_file_path(self, id: int | str) -> str:
        pass

    def _init_root_node(self, init_code, init_meta, node_class):
        if not self.node_list:
            root_id = self._get_id()
            root_file_path = self._get_file_path(root_id)
            root = node_class(init_code, root_id, root_file_path, self.dataset, meta=init_meta)
            self.node_list.append(root)

    @abstractmethod
    def create_node(self, response, parent_node):
        pass

    @abstractmethod
    def select_node(self, k: int):
        pass

    @abstractmethod
    def update_from_child(self, child: CodeNode):
        pass

    def get_best_nodes(self, k: int):
        return sorted(self.node_list, key=lambda x: x.score, reverse=True)[:k]

    @abstractmethod
    def save_report(self):
        pass