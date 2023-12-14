#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/11 18:45
@Author  : alexanderwu
@File    : action_node.py
"""
import re
from typing import Dict, Type, List, Any, Tuple, Optional
import json

from pydantic import BaseModel, create_model, root_validator, validator
#    , model_validator, field_validator
from tenacity import wait_random_exponential, stop_after_attempt, retry

from metagpt.actions import ActionOutput
from metagpt.llm import BaseGPTAPI
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from metagpt.utils.custom_decoder import CustomDecoder

CONSTRAINT = """
- Language: Please use the same language as the user input.
- Format: output wrapped inside [CONTENT][/CONTENT] as format example, nothing else.
"""

SIMPLE_TEMPLATE = """
## context
{context}

-----

## format example
{example}

## nodes: "<node>: <type>  # <comment>"
{instruction}

## constraint
{constraint}

## action
Fill in the above nodes based on the format example.
"""


def dict_to_markdown(d, prefix="-", postfix="\n"):
    markdown_str = ""
    for key, value in d.items():
        markdown_str += f"{prefix} {key}: {value}{postfix}"
    return markdown_str


class ActionNode:
    """ActionNode is a tree of nodes."""
    # Action Strgy
    # - sop: 仅使用一级SOP
    # - complex: 使用一级SOP+自定义策略填槽
    mode: str

    # Action Context
    context: str  # all the context, including all necessary info
    llm: BaseGPTAPI  # LLM with aask interface
    children: dict[str, "ActionNode"]

    # Action Input
    key: str  # Product Requirement / File list / Code
    expected_type: Type  # such as str / int / float etc.
    # context: str  # everything in the history.
    instruction: str  # the instructions should be followed.
    example: Any  # example for In Context-Learning.

    # Action Output
    content: str
    instruct_content: BaseModel

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

    @classmethod
    def from_children(cls, key, nodes: List["ActionNode"]):
        """直接从一系列的子nodes初始化"""
        obj = cls(key, str, "", "")
        obj.add_children(nodes)
        return obj

    def get_children_mapping(self) -> Dict[str, Type]:
        """获得子ActionNode的字典，以key索引"""
        return {k: (v.expected_type, ...) for k, v in self.children.items()}

    def get_self_mapping(self) -> Dict[str, Type]:
        """get self key: type mapping"""
        return {self.key: (self.expected_type, ...)}

    def get_mapping(self, mode="children") -> Dict[str, Type]:
        """get key: type mapping under mode"""
        if mode == "children" or (mode=="auto" and self.children):
            return self.get_children_mapping()
        return self.get_self_mapping()

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

    def to_dict(self, format_func=None, mode="auto") -> Dict:
        """将当前节点与子节点都按照node: format的格式组织成字典"""

        # 如果没有提供格式化函数，使用默认的格式化方式
        if format_func is None:
            format_func = lambda node: f"{node.instruction}"

        # 使用提供的格式化函数来格式化当前节点的值
        formatted_value = format_func(self)

        # 创建当前节点的键值对
        if mode == "children" or (mode == "auto" and self.children):
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
            return f"[{tag}]\n" + text + f"\n[/{tag}]"
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

    def compile(self, context, to="json", mode="children", template=SIMPLE_TEMPLATE) -> str:
        """
        mode: all/root/children
            mode="children": 编译所有子节点为一个统一模板，包括instruction与example
            mode="all": NotImplemented
            mode="root": NotImplemented
        """

        # FIXME: json instruction会带来格式问题，如："Project name": "web_2048  # 项目名称使用下划线",
        self.instruction = self.compile_instruction(to="markdown", mode=mode)
        self.example = self.compile_example(to=to, tag="CONTENT", mode=mode)
        prompt = template.format(context=context, example=self.example, instruction=self.instruction,
                                 constraint=CONSTRAINT)
        return prompt

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def _aask_v1(
        self,
        prompt: str,
        output_class_name: str,
        output_data_mapping: dict,
        system_msgs: Optional[list[str]] = None,
        format="markdown",  # compatible to original format
    ) -> ActionOutput:
        content = await self.llm.aask(prompt, system_msgs)
        logger.debug(content)
        output_class = ActionOutput.create_model_class(output_class_name, output_data_mapping)

        if format == "json":
            pattern = r"\[CONTENT\](\s*\{.*?\}\s*)\[/CONTENT\]"
            matches = re.findall(pattern, content, re.DOTALL)

            for match in matches:
                if match:
                    content = match
                    break

            parsed_data = CustomDecoder(strict=False).decode(content)

        else:  # using markdown parser
            parsed_data = OutputParser.parse_data_with_mapping(content, output_data_mapping)

        logger.debug(parsed_data)
        instruct_content = output_class(**parsed_data)
        return ActionOutput(content, instruct_content)

    def get(self, key):
        return self.instruct_content.dict()[key]

    def set_recursive(self, name, value):
        setattr(self, name, value)
        for _, i in self.children.items():
            i.set_recursive(name, value)

    def set_llm(self, llm):
        self.set_recursive("llm", llm)

    def set_context(self, context):
        self.set_recursive("context", context)

    async def simple_fill(self, to, mode):
        prompt = self.compile(context=self.context, to=to, mode=mode)
        mapping = self.get_mapping(mode)

        class_name = f"{self.key}_AN"
        output = await self._aask_v1(prompt, class_name, mapping, format=to)
        self.content = output.content
        self.instruct_content = output.instruct_content
        return self

    async def fill(self, context, llm, to="json", mode="auto", strgy="simple"):
        """ Fill the node(s) with mode.

        :param context: Everything we should know when filling node.
        :param llm: Large Language Model with pre-defined system message.
        :param to: json/markdown, determine example and output format.
         - json: it's easy to open source LLM with json format
         - markdown: when generating code, markdown is always better
        :param mode: auto/children/root
         - auto: automated fill children's nodes and gather outputs, if no children, fill itself
         - children: fill children's nodes and gather outputs
         - root: fill root's node and gather output
        :param strgy: simple/complex
         - simple: run only once
         - complex: run each node
        :return: self
        """
        self.set_llm(llm)
        self.set_context(context)

        if strgy == "simple":
            return await self.simple_fill(to, mode)
        elif strgy == "complex":
            # 这里隐式假设了拥有children
            tmp = {}
            for _, i in self.children.items():
                child = await i.simple_fill(to, mode)
                tmp.update(child.instruct_content.dict())
            cls = self.create_children_class()
            self.instruct_content = cls(**tmp)
            return self


def action_node_from_tuple_example():
    # 示例：列表中包含元组
    list_of_tuples = [
        ("key1", str, "Instruction 1", "Example 1")
    ]

    # 从列表中创建 ActionNode 实例
    nodes = [ActionNode(*data) for data in list_of_tuples]
    for i in nodes:
        logger.info(i)


if __name__ == '__main__':
    action_node_from_tuple_example()
