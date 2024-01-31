#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/11 18:45
# @Author  : alexanderwu
# @File    : action_node.py
"""
Note:
    You should use typing.List instead of list to do type annotation. Because in the markdown extraction process,
    we can use typing to extract the type of the node, but we cannot use built-in list to extract.
"""

import json
import typing
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from pydantic import BaseModel, Field, create_model, model_validator
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions.action_outcls_registry import register_action_outcls
from metagpt.llm import BaseLLM
from metagpt.logs import logger
from metagpt.provider.postprocess.llm_output_postprocess import llm_output_postprocess
from metagpt.utils.common import OutputParser, general_after_log
from metagpt.utils.human_interaction import HumanInteraction


class ReviewMode(Enum):
    HUMAN = "human"
    AUTO = "auto"


class ReviseMode(Enum):
    HUMAN = "human"  # human revise
    HUMAN_REVIEW = "human_review"  # human-review and auto-revise
    AUTO = "auto"  # auto-review and auto-revise


TAG = "CONTENT"

LANGUAGE_CONSTRAINT = "Language: Please use the same language as Human INPUT."
FORMAT_CONSTRAINT = f"Format: output wrapped inside [{TAG}][/{TAG}] like format example, nothing else."

SIMPLE_TEMPLATE = """
## context
{context}

-----

## format example
{example}

## nodes: "<node>: <type>  # <instruction>"
{instruction}

## constraint
{constraint}

## action
Follow instructions of nodes, generate output and make sure it follows the format example.
"""

REVIEW_TEMPLATE = """
## context
Compare the key's value of nodes_output and the corresponding requirements one by one. If a key's value that does not match the requirement is found, provide the comment content on how to modify it. No output is required for matching keys.

### nodes_output
{nodes_output}

-----

## format example
[{tag}]
{{
    "key1": "comment1",
    "key2": "comment2",
    "keyn": "commentn"
}}
[/{tag}]

## nodes: "<node>: <type>  # <instruction>"
- key1: <class \'str\'> # the first key name of mismatch key
- key2: <class \'str\'> # the second key name of mismatch key
- keyn: <class \'str\'> # the last key name of mismatch key

## constraint
{constraint}

## action
Follow format example's {prompt_schema} format, generate output and make sure it follows the format example.
"""

REVISE_TEMPLATE = """
## context
change the nodes_output key's value to meet its comment and no need to add extra comment.

### nodes_output
{nodes_output}

-----

## format example
{example}

## nodes: "<node>: <type>  # <instruction>"
{instruction}

## constraint
{constraint}

## action
Follow format example's {prompt_schema} format, generate output and make sure it follows the format example.
"""


def dict_to_markdown(d, prefix="- ", kv_sep="\n", postfix="\n"):
    """Converts a dictionary to a markdown string.

    Args:
        d: The dictionary to convert.
        prefix: The prefix to add before each key-value pair.
        kv_sep: The separator between key and value.
        postfix: The postfix to add after each key-value pair.

    Returns:
        A markdown formatted string representing the dictionary.
    """
    markdown_str = ""
    for key, value in d.items():
        markdown_str += f"{prefix}{key}{kv_sep}{value}{postfix}"
    return markdown_str


class ActionNode:
    """Represents a node in an action tree structure.

    Attributes:
        schema (str): A string representing the schema of the node.
        context (str): A string representing the context of the node.
        llm (BaseLLM): An instance of BaseLLM representing the language model.
        children (dict[str, 'ActionNode']): A dictionary of child nodes.
        key (str): A string representing the key of the node.
        expected_type (Type): The expected type of the node's value.
        instruction (str): A string representing the instruction for the node.
        example (Any): An example value for the node.
        content (str): A string representing the content of the node.
        instruct_content (BaseModel): An instance of BaseModel representing the structured content of the node.
    """

    schema: str  # raw/json/markdown, default: ""

    # Action Context
    context: str  # all the context, including all necessary info
    llm: BaseLLM  # LLM with aask interface
    children: dict[str, "ActionNode"]

    # Action Input
    key: str  # Product Requirement / File list / Code
    func: typing.Callable  # 与节点相关联的函数或LLM调用
    params: Dict[str, Type]  # 输入参数的字典，键为参数名，值为参数类型
    expected_type: Type  # such as str / int / float etc.
    # context: str  # everything in the history.
    instruction: str  # the instructions should be followed.
    example: Any  # example for In Context-Learning.

    # Action Output
    content: str
    instruct_content: BaseModel

    # For ActionGraph
    prevs: List["ActionNode"]  # previous nodes
    nexts: List["ActionNode"]  # next nodes

    def __init__(
        self,
        key: str,
        expected_type: Type,
        instruction: str,
        example: Any,
        content: str = "",
        children: dict[str, "ActionNode"] = None,
        schema: str = "",
    ):
        """Initializes an ActionNode object.

        Args:
            key (str): The key of the node.
            expected_type (Type): The expected type of the node's value.
            instruction (str): The instruction for the node.
            example (Any): An example value for the node.
            content (str, optional): The content of the node. Defaults to an empty string.
            children (dict[str, 'ActionNode'], optional): A dictionary of child nodes. Defaults to None.
            schema (str, optional): The schema of the node. Defaults to an empty string.
        """
        self.key = key
        self.expected_type = expected_type
        self.instruction = instruction
        self.example = example
        self.content = content
        self.children = children if children is not None else {}
        self.schema = schema
        self.prevs = []
        self.nexts = []

    def __str__(self):
        return (
            f"{self.key}, {repr(self.expected_type)}, {self.instruction}, {self.example}"
            f", {self.content}, {self.children}"
        )

    def __repr__(self):
        return self.__str__()

    def add_prev(self, node: "ActionNode"):
        """增加前置ActionNode"""
        self.prevs.append(node)

    def add_next(self, node: "ActionNode"):
        """增加后置ActionNode"""
        self.nexts.append(node)

    def add_child(self, node: "ActionNode"):
        """Adds a child node to the current node.

        Args:
            node (ActionNode): The child node to be added.
        """
        self.children[node.key] = node

    def get_child(self, key: str) -> Union["ActionNode", None]:
        """Retrieves a child node by its key.

        Args:
            key (str): The key of the child node to retrieve.

        Returns:
            Union[ActionNode, None]: The retrieved child node if found, otherwise None.
        """
        return self.children.get(key, None)

    def add_children(self, nodes: List["ActionNode"]):
        """Adds multiple child nodes to the current node.

        Args:
            nodes (List[ActionNode]): A list of child nodes to be added.
        """
        for node in nodes:
            self.add_child(node)

    @classmethod
    def from_children(cls, key, nodes: List["ActionNode"]):
        """Creates an ActionNode instance from a list of child nodes.

        Args:
            key: The key for the new ActionNode instance.
            nodes (List[ActionNode]): A list of child nodes.

        Returns:
            ActionNode: The newly created ActionNode instance.
        """
        obj = cls(key, str, "", "")
        obj.add_children(nodes)
        return obj

    def _get_children_mapping(self, exclude=None) -> Dict[str, Any]:
        """Retrieves a mapping of child nodes, supporting nested structures, excluding specified keys.

        Args:
            exclude (optional): A list of keys to exclude from the mapping.

        Returns:
            Dict[str, Tuple[Type, Any]]: A dictionary mapping keys to their expected types and example values, supporting nested structures and excluding specified keys.
        """
        exclude = exclude or []

        def _get_mapping(node: "ActionNode") -> Dict[str, Any]:
            mapping = {}
            for key, child in node.children.items():
                if key in exclude:
                    continue
                # 对于嵌套的子节点，递归调用 _get_mapping
                if child.children:
                    mapping[key] = _get_mapping(child)
                else:
                    mapping[key] = (child.expected_type, Field(default=child.example, description=child.instruction))
            return mapping

        return _get_mapping(self)

    def _get_self_mapping(self) -> Dict[str, Tuple[Type, Any]]:
        """Retrieves a mapping of the current node's key to its type.

        Returns:
            Dict[str, Tuple[Type, Any]]: A dictionary mapping the current node's key to its expected type and example value.
        """
        return {self.key: (self.expected_type, ...)}

    def get_mapping(self, mode="children", exclude=None) -> Dict[str, Tuple[Type, Any]]:
        """Retrieves a mapping of keys to types based on the specified mode.

        Args:
            mode (str, optional): The mode for retrieving the mapping. Defaults to 'children'.
            exclude (optional): A list of keys to exclude from the mapping.

        Returns:
            Dict[str, Tuple[Type, Any]]: A dictionary mapping keys to their expected types and example values based on the specified mode.
        """
        if mode == "children" or (mode == "auto" and self.children):
            return self._get_children_mapping(exclude=exclude)
        return {} if exclude and self.key in exclude else self._get_self_mapping()

    @classmethod
    @register_action_outcls
    def create_model_class(cls, class_name: str, mapping: Dict[str, Tuple[Type, Any]]):
        """Dynamically creates a Pydantic model class for validating result types.

        Args:
            class_name (str): The name for the new model class.
            mapping (Dict[str, Tuple[Type, Any]]): A dictionary mapping field names to their types and default values.

        Returns:
            Type[BaseModel]: The newly created Pydantic model class.
        """

        def check_fields(cls, values):
            required_fields = set(mapping.keys())
            missing_fields = required_fields - set(values.keys())
            if missing_fields:
                raise ValueError(f"Missing fields: {missing_fields}")

            unrecognized_fields = set(values.keys()) - required_fields
            if unrecognized_fields:
                logger.warning(f"Unrecognized fields: {unrecognized_fields}")
            return values

        validators = {"check_missing_fields_validator": model_validator(mode="before")(check_fields)}

        new_fields = {}
        for field_name, field_value in mapping.items():
            if isinstance(field_value, dict):
                # 对于嵌套结构，递归创建模型类
                nested_class_name = f"{class_name}_{field_name}"
                nested_class = cls.create_model_class(nested_class_name, field_value)
                new_fields[field_name] = (nested_class, ...)
            else:
                new_fields[field_name] = field_value

        new_class = create_model(class_name, __validators__=validators, **new_fields)
        return new_class

    def create_class(self, mode: str = "auto", class_name: str = None, exclude=None):
        """Creates a Pydantic model class based on the current node and its children.

        Args:
            mode (str, optional): The mode for creating the class. Defaults to 'auto'.
            class_name (str, optional): The name for the new model class. If not provided, a name is generated.
            exclude (optional): A list of keys to exclude from the class.

        Returns:
            Type[BaseModel]: The newly created Pydantic model class.
        """
        class_name = class_name if class_name else f"{self.key}_AN"
        mapping = self.get_mapping(mode=mode, exclude=exclude)
        return self.create_model_class(class_name, mapping)

    def _create_children_class(self, exclude=None):
        """Creates a Pydantic model class based on the children of the current node.

        Args:
            exclude (optional): A list of keys to exclude from the class.

        Returns:
            Type[BaseModel]: The newly created Pydantic model class based on the children.
        """
        class_name = f"{self.key}_AN"
        mapping = self._get_children_mapping(exclude=exclude)
        return self.create_model_class(class_name, mapping)

    def to_dict(self, format_func=None, mode="auto", exclude=None) -> Dict:
        """Converts the current node and its children to a dictionary.

        Args:
            format_func (optional): A function to format the node values. If not provided, a default formatting is used.
            mode (str, optional): The mode for converting to a dictionary. Defaults to 'auto'.
            exclude (optional): A list of keys to exclude from the dictionary.

        Returns:
            Dict: The dictionary representation of the current node and its children.
        """
        nodes = self._to_dict(format_func=format_func, mode=mode, exclude=exclude)
        if not isinstance(nodes, dict):
            nodes = {self.key: nodes}
        return nodes

    def _to_dict(self, format_func=None, mode="auto", exclude=None) -> Dict:
        """将当前节点与子节点都按照node: format的格式组织成字典"""

        # 如果没有提供格式化函数，则使用默认的格式化函数
        if format_func is None:
            format_func = lambda node: node.instruction

        # 使用提供的格式化函数来格式化当前节点的值
        formatted_value = format_func(self)

        # 创建当前节点的键值对
        if (mode == "children" or mode == "auto") and self.children:
            node_value = {}
        else:
            node_value = formatted_value

        if mode == "root":
            return {self.key: node_value}

        # 递归处理子节点
        exclude = exclude or []
        for child_key, child_node in self.children.items():
            if child_key in exclude:
                continue
            # 递归调用 to_dict 方法并更新节点字典
            child_dict = child_node._to_dict(format_func, mode, exclude)
            node_value[child_key] = child_dict

        return node_value

    def update_instruct_content(self, incre_data: dict[str, Any]):
        """Updates the instruct_content attribute with incremental data.

        Args:
            incre_data (dict[str, Any]): The incremental data to update the instruct_content with.
        """
        assert self.instruct_content
        origin_sc_dict = self.instruct_content.model_dump()
        origin_sc_dict.update(incre_data)
        output_class = self.create_class()
        self.instruct_content = output_class(**origin_sc_dict)

    def keys(self, mode: str = "auto") -> list:
        """Retrieves a list of keys based on the specified mode.

        Args:
            mode (str, optional): The mode for retrieving the keys. Defaults to 'auto'.

        Returns:
            list: A list of keys based on the specified mode.
        """
        if mode == "children" or (mode == "auto" and self.children):
            keys = []
        else:
            keys = [self.key]
        if mode == "root":
            return keys

        for _, child_node in self.children.items():
            keys.append(child_node.key)
        return keys

    def compile_to(self, i: Dict, schema, kv_sep) -> str:
        """Compiles input data to the specified schema format.

        Args:
            i (Dict): The input data to compile.
            schema: The schema to compile the data into.
            kv_sep: The key-value separator to use in the compiled output.

        Returns:
            str: The compiled data in the specified schema format.
        """
        if schema == "json":
            return json.dumps(i, indent=4)
        elif schema == "markdown":
            return dict_to_markdown(i, kv_sep=kv_sep)
        else:
            return str(i)

    def tagging(self, text, schema, tag="") -> str:
        """Wraps text with specified tags based on the schema.

        Args:
            text: The text to wrap.
            schema: The schema to use for wrapping.
            tag (str, optional): The tag to wrap the text with. Defaults to an empty string.

        Returns:
            str: The text wrapped with the specified tag based on the schema.
        """
        if not tag:
            return text
        if schema == "json":
            return f"[{tag}]\n" + text + f"\n[/{tag}]"
        else:  # markdown
            return f"[{tag}]\n" + text + f"\n[/{tag}]"

    def _compile_f(self, schema, mode, tag, format_func, kv_sep, exclude=None) -> str:
        """Compiles node data to the specified format.

        Args:
            schema: The schema to compile the data into.
            mode: The mode for compiling the data.
            tag: The tag to use in the compiled output.
            format_func: The function to format the node values.
            kv_sep: The key-value separator to use in the compiled output.
            exclude (optional): A list of keys to exclude from the compilation.

        Returns:
            str: The compiled node data in the specified format.
        """
        nodes = self.to_dict(format_func=format_func, mode=mode, exclude=exclude)
        text = self.compile_to(nodes, schema, kv_sep)
        return self.tagging(text, schema, tag)

    def compile_instruction(self, schema="markdown", mode="children", tag="", exclude=None) -> str:
        """Compiles instructions to the specified format.

        Args:
            schema (str, optional): The schema to compile the instructions into. Defaults to 'markdown'.
            mode (str, optional): The mode for compiling the instructions. Defaults to 'children'.
            tag (str, optional): The tag to use in the compiled instructions. Defaults to an empty string.
            exclude (optional): A list of keys to exclude from the compilation.

        Returns:
            str: The compiled instructions in the specified format.
        """
        format_func = lambda i: f"{i.expected_type}  # {i.instruction}"
        return self._compile_f(schema, mode, tag, format_func, kv_sep=": ", exclude=exclude)

    def compile_example(self, schema="json", mode="children", tag="", exclude=None) -> str:
        """Compiles examples to the specified format.

        Args:
            schema (str, optional): The schema to compile the examples into. Defaults to 'json'.
            mode (str, optional): The mode for compiling the examples. Defaults to 'children'.
            tag (str, optional): The tag to use in the compiled examples. Defaults to an empty string.
            exclude (optional): A list of keys to exclude from the compilation.

        Returns:
            str: The compiled examples in the specified format.
        """

        # 这里不能使用f-string，因为转译为str后再json.dumps会额外加上引号，无法作为有效的example
        # 错误示例："File list": "['main.py', 'const.py', 'game.py']", 注意这里值不是list，而是str
        format_func = lambda i: i.example
        return self._compile_f(schema, mode, tag, format_func, kv_sep="\n", exclude=exclude)

    def compile(self, context, schema="json", mode="children", template=SIMPLE_TEMPLATE, exclude=[]) -> str:
        """Compiles the node data to a complete template.

        Args:
            context: The context to include in the compiled output.
            schema (str, optional): The schema to compile the data into. Defaults to 'json'.
            mode (str, optional): The mode for compiling the data. Defaults to 'children'.
            template: The template to use for the compiled output.
            exclude (list, optional): A list of keys to exclude from the compilation.

        Returns:
            str: The compiled node data in the specified template.
        """
        if schema == "raw":
            return context + "\n\n## Actions\n" + LANGUAGE_CONSTRAINT + "\n" + self.instruction

        ### 直接使用 pydantic BaseModel 生成 instruction 与 example，仅限 JSON
        # child_class = self._create_children_class()
        # node_schema = child_class.model_json_schema()
        # defaults = {
        #     k: str(v)
        #     for k, v in child_class.model_fields.items()
        #     if k not in exclude
        # }
        # instruction = node_schema
        # example = json.dumps(defaults, indent=4)

        # FIXME: json instruction会带来格式问题，如："Project name": "web_2048  # 项目名称使用下划线",
        # compile example暂时不支持markdown
        instruction = self.compile_instruction(schema="markdown", mode=mode, exclude=exclude)
        example = self.compile_example(schema=schema, tag=TAG, mode=mode, exclude=exclude)
        # nodes = ", ".join(self.to_dict(mode=mode).keys())
        constraints = [LANGUAGE_CONSTRAINT, FORMAT_CONSTRAINT]
        constraint = "\n".join(constraints)

        prompt = template.format(
            context=context,
            example=example,
            instruction=instruction,
            constraint=constraint,
        )
        return prompt

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _aask_v1(
        self,
        prompt: str,
        output_class_name: str,
        output_data_mapping: dict,
        system_msgs: Optional[list[str]] = None,
        schema="markdown",  # compatible to original format
        timeout=3,
    ) -> (str, BaseModel):
        """Asynchronously asks a question and returns the processed output.

        Args:
            prompt (str): The prompt to ask.
            output_class_name (str): The name of the output class for processing the response.
            output_data_mapping (dict): The mapping of the output data.
            system_msgs (Optional[list[str]], optional): System messages to include in the request. Defaults to None.
            schema (str, optional): The schema of the output. Defaults to 'markdown'.
            timeout (int, optional): The timeout for the request. Defaults to 3.

        Returns:
            Tuple[str, BaseModel]: The raw content and the processed output as an instance of the output class.
        """
        content = await self.llm.aask(prompt, system_msgs, timeout=timeout)
        logger.debug(f"llm raw output:\n{content}")
        output_class = self.create_model_class(output_class_name, output_data_mapping)

        if schema == "json":
            parsed_data = llm_output_postprocess(
                output=content, schema=output_class.model_json_schema(), req_key=f"[/{TAG}]"
            )
        else:  # using markdown parser
            parsed_data = OutputParser.parse_data_with_mapping(content, output_data_mapping)

        logger.debug(f"parsed_data:\n{parsed_data}")
        instruct_content = output_class(**parsed_data)
        return content, instruct_content

    def get(self, key):
        """Retrieves the value of the specified key from instruct_content.

        Args:
            key: The key of the value to retrieve.

        Returns:
            The value of the specified key from instruct_content.
        """
        return self.instruct_content.model_dump()[key]

    def set_recursive(self, name, value):
        """Recursively sets the specified attribute to the given value for the node and its children.

        Args:
            name: The name of the attribute to set.
            value: The value to set the attribute to.
        """
        setattr(self, name, value)
        for _, i in self.children.items():
            i.set_recursive(name, value)

    def set_llm(self, llm):
        """Sets the llm attribute for the node and its children.

        Args:
            llm: The llm instance to set.
        """
        self.set_recursive("llm", llm)

    def set_context(self, context):
        """Sets the context attribute for the node and its children.

        Args:
            context: The context to set.
        """
        self.set_recursive("context", context)

    async def simple_fill(self, schema, mode, timeout=3, exclude=None):
        """Fills the node data using a simple strategy.

        Args:
            schema: The schema to use for filling the data.
            mode: The mode for filling the data.
            timeout (int, optional): The timeout for the request. Defaults to 3.
            exclude (optional): A list of keys to exclude from the filling process.

        Returns:
            The current node after filling the data.
        """
        prompt = self.compile(context=self.context, schema=schema, mode=mode, exclude=exclude)

        if schema != "raw":
            mapping = self.get_mapping(mode, exclude=exclude)
            class_name = f"{self.key}_AN"
            content, scontent = await self._aask_v1(prompt, class_name, mapping, schema=schema, timeout=timeout)
            self.content = content
            self.instruct_content = scontent
        else:
            self.content = await self.llm.aask(prompt)
            self.instruct_content = None

        return self

    async def fill(self, context, llm, schema="json", mode="auto", strgy="simple", timeout=3, exclude=[]):
        """Fills the node data based on the specified parameters.

        Args:
            context: The context to use for filling the data.
            llm: The llm instance to use for filling the data.
            schema (str, optional): The schema to use for filling the data. Defaults to 'json'.
                - raw: free form text
                - json: it's easy to open source LLM with json format
                - markdown: when generating code, markdown is always better
            mode (str, optional): The mode for filling the data. Defaults to 'auto'.
                - auto: automated fill children's nodes and gather outputs, if no children, fill itself
                - children: fill children's nodes and gather outputs
                - root: fill root's node and gather output
            strgy (str, optional): The strategy to use for filling the data. Defaults to 'simple'.
                - simple: run only once
                - complex: run each node
            timeout (int, optional): The timeout for the request. Defaults to 3.
            exclude (list, optional): A list of keys to exclude from the filling process.

        Returns:
            The current node after filling the data.
        """
        self.set_llm(llm)
        self.set_context(context)
        if self.schema:
            schema = self.schema

        if strgy == "simple":
            return await self.simple_fill(schema=schema, mode=mode, timeout=timeout, exclude=exclude)
        elif strgy == "complex":
            # 这里隐式假设了拥有children
            tmp = {}
            for _, i in self.children.items():
                if exclude and i.key in exclude:
                    continue
                child = await i.simple_fill(schema=schema, mode=mode, timeout=timeout, exclude=exclude)
                tmp.update(child.instruct_content.model_dump())
            cls = self._create_children_class()
            self.instruct_content = cls(**tmp)
            return self

    async def human_review(self) -> dict[str, str]:
        """Performs a human review of the node data.

        Returns:
            dict[str, str]: The review comments.
        """
        review_comments = HumanInteraction().interact_with_instruct_content(
            instruct_content=self.instruct_content, interact_type="review"
        )

        return review_comments

    def _makeup_nodes_output_with_req(self) -> dict[str, str]:
        """Creates a dictionary of node outputs with their requirements.

        Returns:
            dict[str, str]: A dictionary of node outputs with their requirements.
        """
        instruct_content_dict = self.instruct_content.model_dump()
        nodes_output = {}
        for key, value in instruct_content_dict.items():
            child = self.get_child(key)
            nodes_output[key] = {"value": value, "requirement": child.instruction if child else self.instruction}
        return nodes_output

    async def auto_review(self, template: str = REVIEW_TEMPLATE) -> dict[str, str]:
        """Automatically reviews the node data based on its requirements.

        Args:
            template (str): The template to use for the review.

        Returns:
            dict[str, str]: The review comments.
        """
        nodes_output = self._makeup_nodes_output_with_req()
        """nodes_output format:
        {
            "key": {"value": "output value", "requirement": "key instruction"}
        }
        """
        if not nodes_output:
            return dict()

        prompt = template.format(
            nodes_output=json.dumps(nodes_output, ensure_ascii=False),
            tag=TAG,
            constraint=FORMAT_CONSTRAINT,
            prompt_schema="json",
        )

        content = await self.llm.aask(prompt)
        # Extract the dict of mismatch key and its comment. Due to the mismatch keys are unknown, here use the keys
        # of ActionNode to judge if exist in `content` and then follow the `data_mapping` method to create model class.
        keys = self.keys()
        include_keys = []
        for key in keys:
            if f'"{key}":' in content:
                include_keys.append(key)
        if not include_keys:
            return dict()

        exclude_keys = list(set(keys).difference(include_keys))
        output_class_name = f"{self.key}_AN_REVIEW"
        output_class = self.create_class(class_name=output_class_name, exclude=exclude_keys)
        parsed_data = llm_output_postprocess(
            output=content, schema=output_class.model_json_schema(), req_key=f"[/{TAG}]"
        )
        instruct_content = output_class(**parsed_data)
        return instruct_content.model_dump()

    async def simple_review(self, review_mode: ReviewMode = ReviewMode.AUTO):
        """Performs a simple review of the node data.

        Args:
            review_mode (ReviewMode): The mode for the review.

        Returns:
            The review comments.
        """
        # generate review comments
        if review_mode == ReviewMode.HUMAN:
            review_comments = await self.human_review()
        else:
            review_comments = await self.auto_review()

        if not review_comments:
            logger.warning("There are no review comments")
        return review_comments

    async def review(self, strgy: str = "simple", review_mode: ReviewMode = ReviewMode.AUTO):
        """Reviews the node data based on the specified strategy and mode.

        Args:
            strgy (str): The strategy for the review.
                - simple: run only once
                - complex: run each node
            review_mode (ReviewMode): The mode for the review.

        Returns:
            The review comments.
        """
        if not hasattr(self, "llm"):
            raise RuntimeError("use `review` after `fill`")
        assert review_mode in ReviewMode
        assert self.instruct_content, 'review only support with `schema != "raw"`'

        if strgy == "simple":
            review_comments = await self.simple_review(review_mode)
        elif strgy == "complex":
            # review each child node one-by-one
            review_comments = {}
            for _, child in self.children.items():
                child_review_comment = await child.simple_review(review_mode)
                review_comments.update(child_review_comment)

        return review_comments

    async def human_revise(self) -> dict[str, str]:
        """Performs a human revision of the node data.

        Returns:
            dict[str, str]: The revised contents.
        """
        review_contents = HumanInteraction().interact_with_instruct_content(
            instruct_content=self.instruct_content, mapping=self.get_mapping(mode="auto"), interact_type="revise"
        )
        # re-fill the ActionNode
        self.update_instruct_content(review_contents)
        return review_contents

    def _makeup_nodes_output_with_comment(self, review_comments: dict[str, str]) -> dict[str, str]:
        """Creates a dictionary of node outputs with their review comments.

        Args:
            review_comments (dict[str, str]): The review comments.

        Returns:
            dict[str, str]: A dictionary of node outputs with their review comments.
        """
        instruct_content_dict = self.instruct_content.model_dump()
        nodes_output = {}
        for key, value in instruct_content_dict.items():
            if key in review_comments:
                nodes_output[key] = {"value": value, "comment": review_comments[key]}
        return nodes_output

    async def auto_revise(
        self, revise_mode: ReviseMode = ReviseMode.AUTO, template: str = REVISE_TEMPLATE
    ) -> dict[str, str]:
        """Automatically revises the node data based on review comments.

        Args:
            revise_mode (ReviseMode): The mode for the revision.
            template (str): The template to use for the revision.

        Returns:
            dict[str, str]: The revised contents.
        """
        # generate review comments
        if revise_mode == ReviseMode.AUTO:
            review_comments: dict = await self.auto_review()
        elif revise_mode == ReviseMode.HUMAN_REVIEW:
            review_comments: dict = await self.human_review()

        include_keys = list(review_comments.keys())

        # generate revise content, two-steps
        # step1, find the needed revise keys from review comments to makeup prompt template
        nodes_output = self._makeup_nodes_output_with_comment(review_comments)
        keys = self.keys()
        exclude_keys = list(set(keys).difference(include_keys))
        example = self.compile_example(schema="json", mode="auto", tag=TAG, exclude=exclude_keys)
        instruction = self.compile_instruction(schema="markdown", mode="auto", exclude=exclude_keys)

        prompt = template.format(
            nodes_output=json.dumps(nodes_output, ensure_ascii=False),
            example=example,
            instruction=instruction,
            constraint=FORMAT_CONSTRAINT,
            prompt_schema="json",
        )

        # step2, use `_aask_v1` to get revise structure result
        output_mapping = self.get_mapping(mode="auto", exclude=exclude_keys)
        output_class_name = f"{self.key}_AN_REVISE"
        content, scontent = await self._aask_v1(
            prompt=prompt, output_class_name=output_class_name, output_data_mapping=output_mapping, schema="json"
        )

        # re-fill the ActionNode
        sc_dict = scontent.model_dump()
        self.update_instruct_content(sc_dict)
        return sc_dict

    async def simple_revise(self, revise_mode: ReviseMode = ReviseMode.AUTO) -> dict[str, str]:
        """Performs a simple revision of the node data.

        Args:
            revise_mode (ReviseMode): The mode for the revision.

        Returns:
            dict[str, str]: The revised contents.
        """
        if revise_mode == ReviseMode.HUMAN:
            revise_contents = await self.human_revise()
        else:
            revise_contents = await self.auto_revise(revise_mode)

        return revise_contents

    async def revise(self, strgy: str = "simple", revise_mode: ReviseMode = ReviseMode.AUTO) -> dict[str, str]:
        """Revises the node data based on the specified strategy and mode.

        Args:
            strgy (str): The strategy for the revision.
            revise_mode (ReviseMode): The mode for the revision.

        Returns:
            dict[str, str]: The revised contents.
        """
        if not hasattr(self, "llm"):
            raise RuntimeError("use `revise` after `fill`")
        assert revise_mode in ReviseMode
        assert self.instruct_content, 'revise only support with `schema != "raw"`'

        if strgy == "simple":
            revise_contents = await self.simple_revise(revise_mode)
        elif strgy == "complex":
            # revise each child node one-by-one
            revise_contents = {}
            for _, child in self.children.items():
                child_revise_content = await child.simple_revise(revise_mode)
                revise_contents.update(child_revise_content)
            self.update_instruct_content(revise_contents)

        return revise_contents

    @classmethod
    def from_pydantic(cls, model: Type[BaseModel], key: str = None):
        """Creates an ActionNode tree from a Pydantic model.

        Args:
            model (Type[BaseModel]): The Pydantic model to create the tree from.
            key (str, optional): The key for the root node. If not provided, the model's name is used.

        Returns:
            ActionNode: The root node of the created ActionNode tree.
        """
        key = key or model.__name__
        root_node = cls(key=key, expected_type=Type[model], instruction="", example="")

        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation
            description = field_info.description
            default = field_info.default

            # Recursively handle nested models if needed
            if not isinstance(field_type, typing._GenericAlias) and issubclass(field_type, BaseModel):
                child_node = cls.from_pydantic(field_type, key=field_name)
            else:
                child_node = cls(key=field_name, expected_type=field_type, instruction=description, example=default)

            root_node.add_child(child_node)

        return root_node
