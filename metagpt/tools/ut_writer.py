#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path

from metagpt.config2 import config
from metagpt.provider.openai_api import OpenAILLM as GPTAPI
from metagpt.utils.common import awrite

ICL_SAMPLE = """Interface definition:
```text
Interface Name: Element Tagging
Interface Path: /projects/{project_key}/node-tags
Method: POST

Request parameters:
Path parameters:
project_key

Body parameters:
Name	Type	Required	Default Value	Remarks
nodes	array	Yes		Nodes
	node_key	string	No		Node key
	tags	array	No		Original node tag list
	node_type	string	No		Node type DATASET / RECIPE
operations	array	Yes		
	tags	array	No		Operation tag list
	mode	string	No		Operation type ADD / DELETE

Return data:
Name	Type	Required	Default Value	Remarks
code	integer	Yes		Status code
msg	string	Yes		Prompt message
data	object	Yes		Returned data
list	array	No		Node list true / false
node_type	string	No		Node type DATASET / RECIPE
node_key	string	No		Node key
```

Unit test：
```python
@pytest.mark.parametrize(
"project_key, nodes, operations, expected_msg",
[
("project_key", [{"node_key": "dataset_001", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "success"),
("project_key", [{"node_key": "dataset_002", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["tag1"], "mode": "DELETE"}], "success"),
("", [{"node_key": "dataset_001", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "Missing the required parameter project_key"),
(123, [{"node_key": "dataset_001", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "Incorrect parameter type"),
("project_key", [{"node_key": "a"*201, "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "Request parameter exceeds field boundary")
]
)
def test_node_tags(project_key, nodes, operations, expected_msg):
    pass

# The above is an interface definition and a unit test example.
# Next, please play the role of an expert test manager with 20 years of experience at Google. When I give the interface definition, 
# reply to me with a unit test. There are several requirements:
# 1. Only output one `@pytest.mark.parametrize` and the corresponding test_<interface name> function (inside pass, do not implement).
# -- The function parameter contains expected_msg for result verification.
# 2. The generated test cases use shorter text or numbers and are as compact as possible.
# 3. If comments are needed, use Chinese.

# If you understand, please wait for me to give the interface definition and just answer "Understood" to save tokens.
"""

ACT_PROMPT_PREFIX = """Refer to the test types: such as missing request parameters, field boundary verification, incorrect field type.
Please output 10 test cases within one `@pytest.mark.parametrize` scope.
```text
"""

YFT_PROMPT_PREFIX = """Refer to the test types: such as SQL injection, cross-site scripting (XSS), unauthorized access and privilege escalation, 
authentication and authorization, parameter verification, exception handling, file upload and download.
Please output 10 test cases within one `@pytest.mark.parametrize` scope.
```text
"""

OCR_API_DOC = """```text
Interface Name: OCR recognition
Interface Path: /api/v1/contract/treaty/task/ocr
Method: POST

Request Parameters:
Path Parameters:

Body Parameters:
Name	Type	Required	Default Value	Remarks
file_id	string	Yes		
box	array	Yes		
contract_id	number	Yes		Contract id
start_time	string	No		yyyy-mm-dd
end_time	string	No		yyyy-mm-dd
extract_type	number	No		Recognition type 1- During import 2- After import Default 1

Response Data:
Name	Type	Required	Default Value	Remarks
code	integer	Yes		
message	string	Yes		
data	object	Yes		
```
"""


class UTGenerator:
    """UT Generator: Construct UT through API documentation"""

    def __init__(
        self,
        swagger_file: str,
        ut_py_path: str,
        questions_path: str,
        chatgpt_method: str = "API",
        template_prefix=YFT_PROMPT_PREFIX,
    ) -> None:
        """Initialize UT Generator

        Args:
            swagger_file: path to the swagger file
            ut_py_path: path to store test cases
            questions_path: path to store the template, facilitating subsequent checks
            chatgpt_method: API method
            template_prefix: use the template, default is YFT_UT_PROMPT
        """
        self.swagger_file = swagger_file
        self.ut_py_path = ut_py_path
        self.questions_path = questions_path
        assert chatgpt_method in ["API"], "Invalid chatgpt_method"
        self.chatgpt_method = chatgpt_method

        # ICL: In-Context Learning, provide an example here for GPT to mimic
        self.icl_sample = ICL_SAMPLE
        self.template_prefix = template_prefix

    def get_swagger_json(self) -> dict:
        """Load Swagger JSON from a local file"""
        with open(self.swagger_file, "r", encoding="utf-8") as file:
            swagger_json = json.load(file)
        return swagger_json

    def __para_to_str(self, prop, required, name=""):
        name = name or prop["name"]
        ptype = prop["type"]
        title = prop.get("title", "")
        desc = prop.get("description", "")
        return f'{name}\t{ptype}\t{"Yes" if required else "No"}\t{title}\t{desc}'

    def _para_to_str(self, prop):
        required = prop.get("required", False)
        return self.__para_to_str(prop, required)

    def para_to_str(self, name, prop, prop_object_required):
        required = name in prop_object_required
        return self.__para_to_str(prop, required, name)

    def build_object_properties(self, node, prop_object_required, level: int = 0) -> str:
        """Recursively output properties of object and array[object] types

        Args:
            node (_type_): value of the child item
            prop_object_required (_type_): whether it's a required field
            level: current recursion depth
        """

        doc = ""

        def dive_into_object(node):
            """If it's an object type, recursively output its properties"""
            if node.get("type") == "object":
                sub_properties = node.get("properties", {})
                return self.build_object_properties(sub_properties, prop_object_required, level=level + 1)
            return ""

        if node.get("in", "") in ["query", "header", "formData"]:
            doc += f'{"	" * level}{self._para_to_str(node)}\n'
            doc += dive_into_object(node)
            return doc

        for name, prop in node.items():
            if not isinstance(prop, dict):
                doc += f'{"	" * level}{self._para_to_str(node)}\n'
                break
            doc += f'{"	" * level}{self.para_to_str(name, prop, prop_object_required)}\n'
            doc += dive_into_object(prop)
            if prop["type"] == "array":
                items = prop.get("items", {})
                doc += dive_into_object(items)
        return doc

    def get_tags_mapping(self) -> dict:
        """Process tag and path mappings

        Returns:
            Dict: mapping of tag to path
        """
        swagger_data = self.get_swagger_json()
        paths = swagger_data["paths"]
        tags = {}

        for path, path_obj in paths.items():
            for method, method_obj in path_obj.items():
                for tag in method_obj["tags"]:
                    if tag not in tags:
                        tags[tag] = {}
                    if path not in tags[tag]:
                        tags[tag][path] = {}
                    tags[tag][path][method] = method_obj

        return tags

    async def generate_ut(self, include_tags) -> bool:
        """Generate test case files"""
        tags = self.get_tags_mapping()
        for tag, paths in tags.items():
            if include_tags is None or tag in include_tags:
                await self._generate_ut(tag, paths)
        return True

    def build_api_doc(self, node: dict, path: str, method: str) -> str:
        summary = node["summary"]

        doc = f"API Name: {summary}\nAPI Path: {path}\nMethod: {method.upper()}\n"
        doc += "\nRequest Parameters:\n"
        if "parameters" in node:
            parameters = node["parameters"]
            doc += "Path Parameters:\n"

            # param["in"]: path / formData / body / query / header
            for param in parameters:
                if param["in"] == "path":
                    doc += f'{param["name"]} \n'

            doc += "\nBody Parameters:\n"
            doc += "Name\tType\tRequired\tDefault Value\tRemarks\n"
            for param in parameters:
                if param["in"] == "body":
                    schema = param.get("schema", {})
                    prop_properties = schema.get("properties", {})
                    prop_required = schema.get("required", [])
                    doc += self.build_object_properties(prop_properties, prop_required)
                else:
                    doc += self.build_object_properties(param, [])

        # Display response data information
        doc += "\nResponse Data:\n"
        doc += "Name\tType\tRequired\tDefault Value\tRemarks\n"
        responses = node["responses"]
        response = responses.get("200", {})
        schema = response.get("schema", {})
        properties = schema.get("properties", {})
        required = schema.get("required", {})

        doc += self.build_object_properties(properties, required)
        doc += "\n"
        doc += "```"

        return doc

    async def ask_gpt_and_save(self, question: str, tag: str, fname: str):
        """Generate questions and store both questions and answers"""
        messages = [self.icl_sample, question]
        result = await self.gpt_msgs_to_code(messages=messages)

        await awrite(Path(self.questions_path) / tag / f"{fname}.txt", question)
        data = result.get("code", "") if result else ""
        await awrite(Path(self.ut_py_path) / tag / f"{fname}.py", data)

    async def _generate_ut(self, tag, paths):
        """Process the structure under a data path

        Args:
            tag (_type_): module name
            paths (_type_): Path Object
        """
        for path, path_obj in paths.items():
            for method, node in path_obj.items():
                summary = node["summary"]
                question = self.template_prefix
                question += self.build_api_doc(node, path, method)
                await self.ask_gpt_and_save(question, tag, summary)

    async def gpt_msgs_to_code(self, messages: list) -> str:
        """Choose based on different calling methods"""
        result = ""
        if self.chatgpt_method == "API":
            result = await GPTAPI(config.get_openai_llm()).aask_code(messages=messages)

        return result
