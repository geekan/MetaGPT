#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path

from metagpt.provider.openai_api import OpenAIGPTAPI as GPTAPI

ICL_SAMPLE = '''Interface definition:
```text
Interface Name: Tag Elements
Interface Path: /projects/{project_key}/node-tags
Method: POST

Request Parameters:
Path Parameters:
project_key

Body Parameters:
Name	Type	Required	Default	Value	Description
nodes	array	Yes		Nodes
	node_key	string	No		Node key
	tags	array	No		Original node tag list
	node_type	string	No		Node type DATASET / RECIPE
operations	array	Yes		
	tags	array	No		Operation tag list
	mode	string	No		Operation type ADD / DELETE

Return Data:
Name	Type	Required	Default	Value	Description
code	integer	Yes		Status code
msg	string	Yes		Message
data    object	Yes		Return data
list	array	No		Node list true / false
node_type	string	No		Node type	DATASET / RECIPE
node_key	string	No		Node key
```

Unit Test:
```python
@pytest.mark.parametrize(
"project_key, nodes, operations, expected_msg",
[
("project_key", [{"node_key": "dataset_001", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "success"),
("project_key", [{"node_key": "dataset_002", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["tag1"], "mode": "DELETE"}], "success"),
("", [{"node_key": "dataset_001", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "Missing necessary parameter project_key"),
(123, [{"node_key": "dataset_001", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "Incorrect parameter type"),
("project_key", [{"node_key": "a"*201, "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "Request parameter exceeds field boundary")
]
)
def test_node_tags(project_key, nodes, operations, expected_msg):
    pass
```
The above is an example of interface definition and unit test.
Next, please act as an expert test manager with 20 years of experience at Google. 
After I provide the interface definition, please reply with the unit test. 
There are a few requirements:
1. Only output one `@pytest.mark.parametrize` and the corresponding test_<interface name> function 
   (with a pass inside, not implemented).
   -- The function parameters should include expected_msg for result validation.
2. The generated test cases should use shorter text or numbers and be as concise as possible.
3. If comments are needed, use Chinese.

If you understand, please wait for me to provide the interface definition 
and only reply with "Understood" to save tokens.
'''

ACT_PROMPT_PREFIX = '''Reference test types: such as missing request parameters, field boundary checks, incorrect field types.
Please output 10 test cases within a `@pytest.mark.parametrize` scope.
```text
'''

YFT_PROMPT_PREFIX = '''Reference test types: such as SQL injection, cross-site scripting (XSS), illegal access and unauthorized access, authentication and authorization, parameter verification, exception handling, file upload and download.
Please output 10 test cases within a `@pytest.mark.parametrize` scope.
```text
'''
OCR_API_DOC = '''```text
API Name: OCR Recognition 
API Path: /api/v1/contract/treaty/task/ocr 
Method: POST 

Request Parameters:
Path Parameters:

Body Parameters:
Name	Type	Mandatory	Default Value	Remarks
file_id	string	Yes		
box	array	Yes		
contract_id	number	Yes		Contract ID
start_time	string	No		yyyy-mm-dd
end_time	string	No		yyyy-mm-dd
extract_type	number	No		Recognition Type 1- During Import 2- After Import, Default is 1

Return Data:
Name	Type	Mandatory	Default Value	Remarks
code	integer	Yes		
message	string	Yes		
data	object	Yes		
      
'''

class UTGenerator:
    """UT Generator: Constructs UT from API documentation."""

    def __init__(self, swagger_file: str, ut_py_path: str, questions_path: str,
                 chatgpt_method: str = "API", template_prefix=YFT_PROMPT_PREFIX) -> None:
        """Initializes the UT generator.

        Args:
            swagger_file: Path to the swagger.
            ut_py_path: Path to store test cases.
            questions_path: Path to store templates for further investigation.
            chatgpt_method: API.
            template_prefix: Use template, defaults to YFT_UT_PROMPT.
        """
        self.swagger_file = swagger_file
        self.ut_py_path = ut_py_path
        self.questions_path = questions_path
        assert chatgpt_method in ["API"], "Invalid chatgpt_method"
        self.chatgpt_method = chatgpt_method

        # ICL: In-Context Learning. Here, an example is provided for GPT to follow.
        self.icl_sample = ICL_SAMPLE
        self.template_prefix = template_prefix

    def get_swagger_json(self) -> dict:
        """Loads Swagger JSON from a local file."""
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
        """Recursively outputs properties of object and array[object] types.

        Args:
            node: Value of the sub-item.
            prop_object_required: Whether it's a required item.
            level: Current recursion depth.
        """

        doc = ""

        def dive_into_object(node):
            """If it's an object type, recursively outputs its properties."""
            if node.get("type") == "object":
                sub_properties = node.get("properties", {})
                return self.build_object_properties(sub_properties, prop_object_required, level=level + 1)
            return ""

        if node.get("in", "") in ["query", "header", "formData"]:
            doc += f'{"\t" * level}{self._para_to_str(node)}\n'
            doc += dive_into_object(node)
            return doc

        for name, prop in node.items():
            doc += f'{"\t" * level}{self.para_to_str(name, prop, prop_object_required)}\n'
            doc += dive_into_object(prop)
            if prop["type"] == "array":
                items = prop.get("items", {})
                doc += dive_into_object(items)
        return doc

    def get_tags_mapping(self) -> dict:
        """Handles tag and path mapping.

        Returns:
            Dict: Mapping of tag to path.
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

    def generate_ut(self, include_tags) -> bool:
        """Generates test case files."""
        tags = self.get_tags_mapping()
        for tag, paths in tags.items():
            if include_tags is None or tag in include_tags:
                self._generate_ut(tag, paths)
        return True

    def build_api_doc(self, node: dict, path: str, method: str) -> str:
        summary = node["summary"]

        doc = f"Interface name: {summary}\nInterface path: {path}\nMethod: {method.upper()}\n"
        doc += "\nRequest parameters:\n"
        if "parameters" in node:
            parameters = node["parameters"]
            doc += "Path parameters:\n"

            # param["in"]: path / formData / body / query / header
            for param in parameters:
                if param["in"] == "path":
                    doc += f'{param["name"]} \n'

            doc += "\nBody parameters:\n"
            doc += "Name\tType\tRequired\tDefault\tNotes\n"
            for param in parameters:
                if param["in"] == "body":
                    schema = param.get("schema", {})
                    prop_properties = schema.get("properties", {})
                    prop_required = schema.get("required", [])
                    doc += self.build_object_properties(prop_properties, prop_required)
                else:
                    doc += self.build_object_properties(param, [])

        # Output return data information
        doc += "\nReturn data:\n"
        doc += "Name\tType\tRequired\tDefault\tNotes\n"
        responses = node["responses"]
        response = responses.get("200", {})
        schema = response.get("schema", {})
        properties = schema.get("properties", {})
        required = schema.get("required", {})

        doc += self.build_object_properties(properties, required)
        doc += "\n"
        doc += "```"

        return doc

    def _store(self, data, base, folder, fname):
        """Store data in a file."""
        file_path = self.get_file_path(Path(base) / folder, fname)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(data)

    def ask_gpt_and_save(self, question: str, tag: str, fname: str):
        """Generate a question and save both the question and answer."""
        messages = [self.icl_sample, question]
        result = self.gpt_msgs_to_code(messages=messages)

        self._store(question, self.questions_path, tag, f"{fname}.txt")
        self._store(result, self.ut_py_path, tag, f"{fname}.py")

    def _generate_ut(self, tag, paths):
        """Process the structure under the data path.

        Args:
            tag: Module name.
            paths: Path Object.
        """
        for path, path_obj in paths.items():
            for method, node in path_obj.items():
                summary = node["summary"]
                question = self.template_prefix
                question += self.build_api_doc(node, path, method)
                self.ask_gpt_and_save(question, tag, summary)

    def gpt_msgs_to_code(self, messages: list) -> str:
        """Choose based on different call methods."""
        result = ''
        if self.chatgpt_method == "API":
            result = GPTAPI().ask_code(msgs=messages)

        return result

    def get_file_path(self, base: Path, fname: str):
        """Save to different file paths.

        Args:
            base (str): Path.
            fname (str): File name.
        """
        path = Path(base)
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / fname
        return str(file_path)
