#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/11 18:45
@Author  : alexanderwu
@File    : action_node.py
"""
from typing import Dict, Type, List, Any
import json

from pydantic import BaseModel, create_model, root_validator, validator
#    , model_validator, field_validator

from metagpt.logs import logger


def dict_to_markdown(d, prefix="##", postfix="\n\n"):
    markdown_str = ""
    for key, value in d.items():
        markdown_str += f"{prefix} {key}: {value}{postfix}"
    return markdown_str


class ActionNode:
    """ActionNode is a tree of nodes."""

    # Action Inputs
    key: str  # Product Requirement / File list / Code
    expected_type: Type  # such as str / int / float etc.
    # context: str  # everything in the history.
    instruction: str  # the instructions should be followed.
    example: str  # example for In Context-Learning.

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

    def add_childs(self, nodes: List["ActionNode"]):
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

    def compile_to(self, i: Dict, to="raw") -> str:
        if to == "json":
            return json.dumps(i, indent=4)
        elif to == "markdown":
            return dict_to_markdown(i)
        else:
            return str(i)

    def compile_instruction(self, to="raw", mode="children") -> str:
        """compile to raw/json/markdown template with all/root/children nodes"""
        format_func = lambda i: f"{i.expected_type}  # {i.instruction}"
        nodes = self.to_dict(format_func=format_func, mode=mode)
        return self.compile_to(nodes, to)

    def compile_example(self, to="raw", mode="all") -> str:
        """compile to raw/json/markdown examples with all/root/children nodes"""
        format_func = lambda i: f"{i.example}"
        nodes = self.to_dict(format_func=format_func, mode=mode)
        return self.compile_to(nodes, to)

    def compile(self, to="raw", mode="all") -> str:
        pass

    def run(self):
        """运行这个ActionNode，可以采用不同策略，比如只运行子节点"""
        pass


IMPLEMENTATION_APPROACH = ActionNode(
    key="implementation_approach",
    expected_type=str,
    instruction="Analyze the difficult points of the requirements, select the appropriate open-source framework",
    example="We will ..."
)

PROJECT_NAME = ActionNode(
    key="project_name",
    expected_type=str,
    instruction="The project name with underline",
    example="game_2048"
)

FILE_LIST = ActionNode(
    key="file_list",
    expected_type=List[str],
    instruction="Only need relative paths. ALWAYS write a main.py or app.py here",
    example="['main.py', 'const.py', 'utils.py']"
)

DATA_STRUCTURES_AND_INTERFACES = ActionNode(
    key="data_structures_and_interfaces",
    expected_type=str,
    instruction="Use mermaid classDiagram code syntax, including classes (INCLUDING __init__ method) and functions "
     "(with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. "
     "The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design.",
    example="""classDiagram
class Game{{
    +int score
}}
...
Game "1" -- "1" Food: has"""
)

PROGRAM_CALL_FLOW = ActionNode(
    key="program_call_flow",
    expected_type=str,
    instruction="Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE "
                "accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.",
    example="""sequenceDiagram
participant M as Main
...
G->>M: end game"""
)

ANYTHING_UNCLEAR = ActionNode(
    key="anything_unclear",
    expected_type=str,
    instruction="Mention unclear project aspects, then try to clarify it.",
    example="Clarification needed on third-party API integration, ..."
)


ACTION_NODES = [
    IMPLEMENTATION_APPROACH,
    PROJECT_NAME,
    FILE_LIST,
    DATA_STRUCTURES_AND_INTERFACES,
    PROGRAM_CALL_FLOW,
    ANYTHING_UNCLEAR
]


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


def main():
    write_design_node = ActionNode("WriteDesign", str, "", "")
    write_design_node.add_childs(ACTION_NODES)
    instruction = write_design_node.compile_instruction(to="markdown")
    logger.info(instruction)
    logger.info(write_design_node.compile_example())


if __name__ == '__main__':
    main()
