#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/11 18:45
@Author  : alexanderwu
@File    : action_node.py
"""
from typing import Dict, Type, List, Any, Tuple
import json

from pydantic import BaseModel, create_model, root_validator, validator
#    , model_validator, field_validator

from metagpt.logs import logger


SIMPLE_TEMPLATE = """
## example
{example}

## instruction
{instruction}
"""


def dict_to_markdown(d, prefix="###", postfix="\n"):
    markdown_str = ""
    for key, value in d.items():
        markdown_str += f"{prefix} {key}: {value}{postfix}"
    return markdown_str


class ActionNode:
    """ActionNode is a tree of nodes."""
    # 应该是定义子任务，收集子任务结果，并且父任务同时执行吗？
    # 初期只提供两种模式，一种是用父任务compile，一种是用子任务逐个执行
    # 1. context、example、instruction-nodes、instruction-action
    # 2. context、example

    # Action Inputs
    key: str  # Product Requirement / File list / Code
    expected_type: Type  # such as str / int / float etc.
    # context: str  # everything in the history.
    instruction: str  # the instructions should be followed.
    example: Any  # example for In Context-Learning.

    # Action Outputs
    content: str
    instruct_content: BaseModel
    children: dict[str, "ActionNode"]

    def __init__(self, key, expected_type, instruction, example, content="",
                 children=None):
        self.key = key
        self.expected_type = expected_type
        self.instruction = instruction
        self.example = example
        self.content = content
        self.children = children if children is not None else {}

    def __str__(self):
        return f"{self.key}, {self.expected_type}, {self.instruction}, {self.example}" \
               f", {self.content}, {self.children}"

    def __repr__(self):
        return self.__str__()

    def add_child(self, node: "ActionNode"):
        """增加子ActionNode"""
        self.children[node.key] = node

    def add_children(self, nodes: List["ActionNode"]):
        """批量增加子ActionNode"""
        for node in nodes:
            self.add_child(node)

    def get_children_mapping(self) -> Dict[str, Type]:
        """获得子ActionNode的字典，以key索引"""
        return {k: v.expected_type for k, v in self.children.items()}

    @classmethod
    def create_model_class(cls, class_name: str, mapping: Dict[str, Type]):
        """基于pydantic v1的模型动态生成，用来检验结果类型正确性"""
        new_class = create_model(class_name, **mapping)

        @validator("*", allow_reuse=True)
        def check_name(v, field):
            if field.name not in mapping.keys():
                raise ValueError(f"Unrecognized block: {field.name}")
            return v

        @root_validator(pre=True, allow_reuse=True)
        def check_missing_fields(values):
            required_fields = set(mapping.keys())
            missing_fields = required_fields - set(values.keys())
            if missing_fields:
                raise ValueError(f"Missing fields: {missing_fields}")
            return values

        new_class.__validator_check_name = classmethod(check_name)
        new_class.__root_validator_check_missing_fields = classmethod(check_missing_fields)
        return new_class

    @classmethod
    def create_model_class_v2(cls, class_name: str, mapping: Dict[str, Type]):
        """基于pydantic v2的模型动态生成，用来检验结果类型正确性，待验证"""
        new_class = create_model(class_name, **mapping)

        @model_validator(mode='before')
        def check_missing_fields(data):
            required_fields = set(mapping.keys())
            missing_fields = required_fields - set(data.keys())
            if missing_fields:
                raise ValueError(f"Missing fields: {missing_fields}")
            return data

        @field_validator('*')
        def check_name(v: Any, field: str) -> Any:
            if field not in mapping.keys():
                raise ValueError(f"Unrecognized block: {field}")
            return v

        new_class.__model_validator_check_missing_fields = classmethod(check_missing_fields)
        new_class.__field_validator_check_name = classmethod(check_name)
        return new_class

    def create_children_class(self):
        """使用object内有的字段直接生成model_class"""
        class_name = f"{self.key}_AN"
        mapping = self.get_children_mapping()
        return self.create_model_class(class_name, mapping)

    def to_dict(self, format_func=None, mode="all") -> Dict:
        # 如果没有提供格式化函数，使用默认的格式化方式
        if format_func is None:
            format_func = lambda node: f"{node.instruction}"

        # 使用提供的格式化函数来格式化当前节点的值
        formatted_value = format_func(self)

        # 创建当前节点的键值对
        if mode == "children":
            node_dict = {}
        else:
            node_dict = {self.key: formatted_value}

        if mode == "root":
            return node_dict

        # 遍历子节点并递归调用 to_dict 方法
        for child_key, child_node in self.children.items():
            node_dict.update(child_node.to_dict(format_func))

        return node_dict

    def compile_to(self, i: Dict, to) -> str:
        if to == "json":
            return json.dumps(i, indent=4)
        elif to == "markdown":
            return dict_to_markdown(i)
        else:
            return str(i)

    def tagging(self, text, to, tag="") -> str:
        if not tag:
            return text
        if to == "json":
            return f"[{tag}]\n" + "{" + text + "}" + f"\n[/{tag}]"
        else:
            return f"[{tag}]\n" + text + f"\n[/{tag}]"

    def _compile_f(self, to, mode, tag, format_func) -> str:
        nodes = self.to_dict(format_func=format_func, mode=mode)
        text = self.compile_to(nodes, to)
        return self.tagging(text, to, tag)

    def compile_instruction(self, to="raw", mode="children", tag="") -> str:
        """compile to raw/json/markdown template with all/root/children nodes"""
        format_func = lambda i: f"{i.expected_type}  # {i.instruction}"
        return self._compile_f(to, mode, tag, format_func)

    def compile_example(self, to="raw", mode="children", tag="") -> str:
        """compile to raw/json/markdown examples with all/root/children nodes"""

        # 这里不能使用f-string，因为转译为str后再json.dumps会额外加上引号，无法作为有效的example
        # 错误示例："File list": "['main.py', 'const.py', 'game.py']", 注意这里值不是list，而是str
        format_func = lambda i: i.example
        return self._compile_f(to, mode, tag, format_func)

    def compile(self, mode="children") -> Tuple[str, str]:
        """
        mode: all/root/children
            mode="children": 编译所有子节点为一个统一模板，包括instruction与example
            mode="all": NotImplemented
            mode="root": NotImplemented
        """
        self.instruction = self.compile_instruction(to="json", mode=mode)
        self.example = self.compile_example(to="json", tag="CONTENT", mode=mode)
        # prompt = template.format(example=self.example, instruction=self.instruction)
        return self.instruction, self.example

    def run(self):
        """运行这个ActionNode，可以采用不同策略，比如只运行子节点"""

        # 需要传入llm，并且实际在ActionNode中执行。需要规划好具体的执行方法
        raise NotImplementedError


def action_node_from_tuple_example():
    # 示例：列表中包含元组
    list_of_tuples = [
        ("key1", str, "Instruction 1", "Example 1", "Content 1", {"child1": ...}),
        ("key2", int, "Instruction 2", "Example 2", "Content 2"),
        ("key3", int, "Instruction 3", "Example 3")
    ]

    # 从列表中创建 ActionNode 实例
    nodes = [ActionNode(*data) for data in list_of_tuples]
    for i in nodes:
        logger.info(i)


if __name__ == '__main__':
    action_node_from_tuple_example()
