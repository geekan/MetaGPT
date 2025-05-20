import ast
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/11 18:45
@Author  : alexanderwu
@File    : action_node.py

NOTE: You should use typing.List instead of list to do type annotation. Because in the markdown extraction process,
  we can use typing to extract the type of the node, but we cannot use built-in list to extract.
"""
import json
import re
import typing
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from pydantic import BaseModel, Field, create_model, model_validator
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions.action_outcls_registry import register_action_outcls
from metagpt.const import MARKDOWN_TITLE_PREFIX, USE_CONFIG_TIMEOUT
from metagpt.exp_pool import exp_cache
from metagpt.exp_pool.serializers import ActionNodeSerializer
from metagpt.llm import BaseLLM
from metagpt.logs import logger
from metagpt.provider.postprocess.llm_output_postprocess import llm_output_postprocess
from metagpt.utils.common import OutputParser, general_after_log
from metagpt.utils.human_interaction import HumanInteraction
from metagpt.utils.sanitize import sanitize


class ReviewMode(Enum):
    HUMAN = "human"
    AUTO = "auto"


class ReviseMode(Enum):
    HUMAN = "human"  # human revise
    HUMAN_REVIEW = "human_review"  # human-review and auto-revise
    AUTO = "auto"  # auto-review and auto-revise


TAG = "CONTENT"


class FillMode(Enum):
    CODE_FILL = "code_fill"
    XML_FILL = "xml_fill"
    SINGLE_FILL = "single_fill"


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


def dict_to_markdown(d, prefix=MARKDOWN_TITLE_PREFIX, kv_sep="\n", postfix="\n"):
    markdown_str = ""
    for key, value in d.items():
        markdown_str += f"{prefix}{key}{kv_sep}{value}{postfix}"
    return markdown_str


class ActionNode:
    """ActionNode is a tree of nodes."""

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
        """增加子ActionNode"""
        self.children[node.key] = node

    def get_child(self, key: str) -> Union["ActionNode", None]:
        return self.children.get(key, None)

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

    def _get_children_mapping(self, exclude=None) -> Dict[str, Any]:
        """获得子ActionNode的字典，以key索引，支持多级结构。"""
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
        """get self key: type mapping"""
        return {self.key: (self.expected_type, ...)}

    def get_mapping(self, mode="children", exclude=None) -> Dict[str, Tuple[Type, Any]]:
        """get key: type mapping under mode"""
        if mode == "children" or (mode == "auto" and self.children):
            return self._get_children_mapping(exclude=exclude)
        return {} if exclude and self.key in exclude else self._get_self_mapping()

    @classmethod
    @register_action_outcls
    def create_model_class(cls, class_name: str, mapping: Dict[str, Tuple[Type, Any]]):
        """基于pydantic v2的模型动态生成，用来检验结果类型正确性"""

        def check_fields(cls, values):
            all_fields = set(mapping.keys())
            required_fields = set()
            for k, v in mapping.items():
                type_v, field_info = v
                if ActionNode.is_optional_type(type_v):
                    continue
                required_fields.add(k)

            missing_fields = required_fields - set(values.keys())
            if missing_fields:
                raise ValueError(f"Missing fields: {missing_fields}")

            unrecognized_fields = set(values.keys()) - all_fields
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
        class_name = class_name if class_name else f"{self.key}_AN"
        mapping = self.get_mapping(mode=mode, exclude=exclude)
        return self.create_model_class(class_name, mapping)

    def _create_children_class(self, exclude=None):
        """使用object内有的字段直接生成model_class"""
        class_name = f"{self.key}_AN"
        mapping = self._get_children_mapping(exclude=exclude)
        return self.create_model_class(class_name, mapping)

    def to_dict(self, format_func=None, mode="auto", exclude=None) -> Dict:
        """将当前节点与子节点都按照node: format的格式组织成字典"""
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
        assert self.instruct_content
        origin_sc_dict = self.instruct_content.model_dump()
        origin_sc_dict.update(incre_data)
        output_class = self.create_class()
        self.instruct_content = output_class(**origin_sc_dict)

    def keys(self, mode: str = "auto") -> list:
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
        if schema == "json":
            return json.dumps(i, indent=4, ensure_ascii=False)
        elif schema == "markdown":
            return dict_to_markdown(i, kv_sep=kv_sep)
        else:
            return str(i)

    def tagging(self, text, schema, tag="") -> str:
        if not tag:
            return text
        return f"[{tag}]\n{text}\n[/{tag}]"

    def _compile_f(self, schema, mode, tag, format_func, kv_sep, exclude=None) -> str:
        nodes = self.to_dict(format_func=format_func, mode=mode, exclude=exclude)
        text = self.compile_to(nodes, schema, kv_sep)
        return self.tagging(text, schema, tag)

    def compile_instruction(self, schema="markdown", mode="children", tag="", exclude=None) -> str:
        """compile to raw/json/markdown template with all/root/children nodes"""
        format_func = lambda i: f"{i.expected_type}  # {i.instruction}"
        return self._compile_f(schema, mode, tag, format_func, kv_sep=": ", exclude=exclude)

    def compile_example(self, schema="json", mode="children", tag="", exclude=None) -> str:
        """compile to raw/json/markdown examples with all/root/children nodes"""

        # 这里不能使用f-string，因为转译为str后再json.dumps会额外加上引号，无法作为有效的example
        # 错误示例："File list": "['main.py', 'const.py', 'game.py']", 注意这里值不是list，而是str
        format_func = lambda i: i.example
        return self._compile_f(schema, mode, tag, format_func, kv_sep="\n", exclude=exclude)

    def compile(self, context, schema="json", mode="children", template=SIMPLE_TEMPLATE, exclude=[]) -> str:
        """
        mode: all/root/children
            mode="children": 编译所有子节点为一个统一模板，包括instruction与example
            mode="all": NotImplemented
            mode="root": NotImplemented
        schmea: raw/json/markdown
            schema="raw": 不编译，context, lang_constaint, instruction
            schema="json"：编译context, example(json), instruction(markdown), constraint, action
            schema="markdown": 编译context, example(markdown), instruction(markdown), constraint, action
        """
        if schema == "raw":
            return f"{context}\n\n## Actions\n{LANGUAGE_CONSTRAINT}\n{self.instruction}"

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
        images: Optional[Union[str, list[str]]] = None,
        system_msgs: Optional[list[str]] = None,
        schema="markdown",  # compatible to original format
        timeout=USE_CONFIG_TIMEOUT,
    ) -> (str, BaseModel):
        """Use ActionOutput to wrap the output of aask"""
        content = await self.llm.aask(prompt, system_msgs, images=images, timeout=timeout)
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
        return self.instruct_content.model_dump()[key]

    def set_recursive(self, name, value):
        setattr(self, name, value)
        for _, i in self.children.items():
            i.set_recursive(name, value)

    def set_llm(self, llm):
        self.set_recursive("llm", llm)

    def set_context(self, context):
        self.set_recursive("context", context)

    async def simple_fill(
        self, schema, mode, images: Optional[Union[str, list[str]]] = None, timeout=USE_CONFIG_TIMEOUT, exclude=None
    ):
        prompt = self.compile(context=self.context, schema=schema, mode=mode, exclude=exclude)
        if schema != "raw":
            mapping = self.get_mapping(mode, exclude=exclude)
            class_name = f"{self.key}_AN"
            content, scontent = await self._aask_v1(
                prompt, class_name, mapping, images=images, schema=schema, timeout=timeout
            )
            self.content = content
            self.instruct_content = scontent
        else:
            self.content = await self.llm.aask(prompt)
            self.instruct_content = None

        return self

    def get_field_name(self):
        """
        Get the field name from the Pydantic model associated with this ActionNode.
        """
        model_class = self.create_class()
        fields = model_class.model_fields

        # Assuming there's only one field in the model
        if len(fields) == 1:
            return next(iter(fields))

        # If there are multiple fields, we might want to use self.key to find the right one
        return self.key

    def get_field_names(self):
        """
        Get the field names associated with this ActionNode's Pydantic model.
        """
        model_class = self.create_class()
        return model_class.model_fields.keys()

    def get_field_types(self):
        """
        Get the field types associated with this ActionNode's Pydantic model.
        """
        model_class = self.create_class()
        return {field_name: field.annotation for field_name, field in model_class.model_fields.items()}

    def xml_compile(self, context):
        """
        Compile the prompt to make it easier for the model to understand the xml format.
        """
        field_names = self.get_field_names()
        # Construct the example using the field names
        examples = []
        for field_name in field_names:
            examples.append(f"<{field_name}>content</{field_name}>")

        # Join all examples into a single string
        example_str = "\n".join(examples)
        # Add the example to the context
        context += f"""
### Response format (must be strictly followed): All content must be enclosed in the given XML tags, ensuring each opening <tag> has a corresponding closing </tag>, with no incomplete or self-closing tags allowed.\n
{example_str}
"""
        return context

    async def code_fill(
        self, context: str, function_name: Optional[str] = None, timeout: int = USE_CONFIG_TIMEOUT
    ) -> Dict[str, str]:
        """
        Fill CodeBlock Using ``` ```
        """
        field_name = self.get_field_name()
        prompt = context
        content = await self.llm.aask(prompt, timeout=timeout)
        extracted_code = sanitize(code=content, entrypoint=function_name)
        result = {field_name: extracted_code}
        return result

    async def single_fill(self, context: str, images: Optional[Union[str, list[str]]] = None) -> Dict[str, str]:
        field_name = self.get_field_name()
        prompt = context
        content = await self.llm.aask(prompt, images=images)
        result = {field_name: content}
        return result

    async def xml_fill(self, context: str, images: Optional[Union[str, list[str]]] = None) -> Dict[str, Any]:
        """
        Fill context with XML tags and convert according to field types, including string, integer, boolean, list and dict types
        """
        field_names = self.get_field_names()
        field_types = self.get_field_types()

        extracted_data: Dict[str, Any] = {}
        content = await self.llm.aask(context, images=images)

        for field_name in field_names:
            pattern = rf"<{field_name}>(.*?)</{field_name}>"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                raw_value = match.group(1).strip()
                field_type = field_types.get(field_name)

                if field_type == str:
                    extracted_data[field_name] = raw_value
                elif field_type == int:
                    try:
                        extracted_data[field_name] = int(raw_value)
                    except ValueError:
                        extracted_data[field_name] = 0  # 或者其他默认值
                elif field_type == bool:
                    extracted_data[field_name] = raw_value.lower() in ("true", "yes", "1", "on", "True")
                elif field_type == list:
                    try:
                        extracted_data[field_name] = ast.literal_eval(raw_value)
                        if not isinstance(extracted_data[field_name], list):
                            raise ValueError
                    except:
                        extracted_data[field_name] = []  # 默认空列表
                elif field_type == dict:
                    try:
                        extracted_data[field_name] = ast.literal_eval(raw_value)
                        if not isinstance(extracted_data[field_name], dict):
                            raise ValueError
                    except:
                        extracted_data[field_name] = {}  # 默认空字典

        return extracted_data

    @exp_cache(serializer=ActionNodeSerializer())
    async def fill(
        self,
        *,
        req,
        llm,
        schema="json",
        mode="auto",
        strgy="simple",
        images: Optional[Union[str, list[str]]] = None,
        timeout=USE_CONFIG_TIMEOUT,
        exclude=[],
        function_name: str = None,
    ):
        """Fill the node(s) with mode.

        :param req: Everything we should know when filling node.
        :param llm: Large Language Model with pre-defined system message.
        :param schema: json/markdown, determine example and output format.
         - raw: free form text
         - json: it's easy to open source LLM with json format
         - markdown: when generating code, markdown is always better
        :param mode: auto/children/root
         - auto: automated fill children's nodes and gather outputs, if no children, fill itself
         - children: fill children's nodes and gather outputs
         - root: fill root's node and gather output
        :param strgy: simple/complex
         - simple: run only once
         - complex: run each node
        :param images: the list of image url or base64 for gpt4-v
        :param timeout: Timeout for llm invocation.
        :param exclude: The keys of ActionNode to exclude.
        :return: self
        """
        self.set_llm(llm)
        self.set_context(req)
        if self.schema:
            schema = self.schema

        if mode == FillMode.CODE_FILL.value:
            result = await self.code_fill(context, function_name, timeout)
            self.instruct_content = self.create_class()(**result)
            return self

        elif mode == FillMode.XML_FILL.value:
            context = self.xml_compile(context=self.context)
            result = await self.xml_fill(context, images=images)
            self.instruct_content = self.create_class()(**result)
            return self

        elif mode == FillMode.SINGLE_FILL.value:
            result = await self.single_fill(context, images=images)
            self.instruct_content = self.create_class()(**result)
            return self

        if strgy == "simple":
            return await self.simple_fill(schema=schema, mode=mode, images=images, timeout=timeout, exclude=exclude)
        elif strgy == "complex":
            # 这里隐式假设了拥有children
            tmp = {}
            for _, i in self.children.items():
                if exclude and i.key in exclude:
                    continue
                child = await i.simple_fill(schema=schema, mode=mode, images=images, timeout=timeout, exclude=exclude)
                tmp.update(child.instruct_content.model_dump())
            cls = self._create_children_class()
            self.instruct_content = cls(**tmp)
            return self

    async def human_review(self) -> dict[str, str]:
        review_comments = HumanInteraction().interact_with_instruct_content(
            instruct_content=self.instruct_content, interact_type="review"
        )

        return review_comments

    def _makeup_nodes_output_with_req(self) -> dict[str, str]:
        instruct_content_dict = self.instruct_content.model_dump()
        nodes_output = {}
        for key, value in instruct_content_dict.items():
            child = self.get_child(key)
            nodes_output[key] = {"value": value, "requirement": child.instruction if child else self.instruction}
        return nodes_output

    async def auto_review(self, template: str = REVIEW_TEMPLATE) -> dict[str, str]:
        """use key's output value and its instruction to review the modification comment"""
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
        # generate review comments
        if review_mode == ReviewMode.HUMAN:
            review_comments = await self.human_review()
        else:
            review_comments = await self.auto_review()

        if not review_comments:
            logger.warning("There are no review comments")
        return review_comments

    async def review(self, strgy: str = "simple", review_mode: ReviewMode = ReviewMode.AUTO):
        """only give the review comment of each exist and mismatch key

        :param strgy: simple/complex
         - simple: run only once
         - complex: run each node
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
        review_contents = HumanInteraction().interact_with_instruct_content(
            instruct_content=self.instruct_content, mapping=self.get_mapping(mode="auto"), interact_type="revise"
        )
        # re-fill the ActionNode
        self.update_instruct_content(review_contents)
        return review_contents

    def _makeup_nodes_output_with_comment(self, review_comments: dict[str, str]) -> dict[str, str]:
        instruct_content_dict = self.instruct_content.model_dump()
        nodes_output = {}
        for key, value in instruct_content_dict.items():
            if key in review_comments:
                nodes_output[key] = {"value": value, "comment": review_comments[key]}
        return nodes_output

    async def auto_revise(
        self, revise_mode: ReviseMode = ReviseMode.AUTO, template: str = REVISE_TEMPLATE
    ) -> dict[str, str]:
        """revise the value of incorrect keys"""
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
        if revise_mode == ReviseMode.HUMAN:
            revise_contents = await self.human_revise()
        else:
            revise_contents = await self.auto_revise(revise_mode)

        return revise_contents

    async def revise(self, strgy: str = "simple", revise_mode: ReviseMode = ReviseMode.AUTO) -> dict[str, str]:
        """revise the content of ActionNode and update the instruct_content

        :param strgy: simple/complex
         - simple: run only once
         - complex: run each node
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
        """
        Creates an ActionNode tree from a Pydantic model.

        Args:
            model (Type[BaseModel]): The Pydantic model to convert.

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

    @staticmethod
    def is_optional_type(tp) -> bool:
        """Return True if `tp` is `typing.Optional[...]`"""
        if typing.get_origin(tp) is Union:
            args = typing.get_args(tp)
            non_none_types = [arg for arg in args if arg is not type(None)]
            return len(non_none_types) == 1 and len(args) == 2
        return False
