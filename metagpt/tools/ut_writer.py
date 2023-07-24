#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path

from metagpt.provider.openai_api import OpenAIGPTAPI as GPTAPI

ICL_SAMPLE = '''接口定义：
```text
接口名称：元素打标签
接口路径：/projects/{project_key}/node-tags
Method：POST	

请求参数：
路径参数：
project_key

Body参数：
名称	类型	是否必须	默认值	备注
nodes	array	是		节点
	node_key	string	否		节点key
	tags	array	否		节点原标签列表
	node_type	string	否		节点类型 DATASET / RECIPE
operations	array	是		
	tags	array	否		操作标签列表
	mode	string	否		操作类型 ADD / DELETE

返回数据：
名称	类型	是否必须	默认值	备注
code	integer	是		状态码
msg	string	是		提示信息
data	object	是		返回数据
list	array	否		node列表 true / false
node_type	string	否		节点类型	DATASET / RECIPE
node_key	string	否		节点key
```

单元测试：
```python
@pytest.mark.parametrize(
"project_key, nodes, operations, expected_msg",
[
("project_key", [{"node_key": "dataset_001", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "success"),
("project_key", [{"node_key": "dataset_002", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["tag1"], "mode": "DELETE"}], "success"),
("", [{"node_key": "dataset_001", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "缺少必要的参数 project_key"),
(123, [{"node_key": "dataset_001", "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "参数类型不正确"),
("project_key", [{"node_key": "a"*201, "tags": ["tag1", "tag2"], "node_type": "DATASET"}], [{"tags": ["new_tag1"], "mode": "ADD"}], "请求参数超出字段边界")
]
)
def test_node_tags(project_key, nodes, operations, expected_msg):
    pass
```
以上是一个 接口定义 与 单元测试 样例。
接下来，请你扮演一个Google 20年经验的专家测试经理，在我给出 接口定义 后，回复我单元测试。有几个要求
1. 只输出一个 `@pytest.mark.parametrize` 与对应的test_<接口名>函数（内部pass，不实现）
-- 函数参数中包含expected_msg，用于结果校验
2. 生成的测试用例使用较短的文本或数字，并且尽量紧凑
3. 如果需要注释，使用中文

如果你明白了，请等待我给出接口定义，并只回答"明白"，以节省token
'''

ACT_PROMPT_PREFIX = '''参考测试类型：如缺少请求参数，字段边界校验，字段类型不正确
请在一个 `@pytest.mark.parametrize` 作用域内输出10个测试用例
```text
'''

YFT_PROMPT_PREFIX = '''参考测试类型：如SQL注入，跨站点脚本（XSS），非法访问和越权访问，认证和授权，参数验证，异常处理，文件上传和下载
请在一个 `@pytest.mark.parametrize` 作用域内输出10个测试用例
```text
'''

OCR_API_DOC = '''```text
接口名称：OCR识别 
接口路径：/api/v1/contract/treaty/task/ocr 
Method：POST 

请求参数：
路径参数：

Body参数：
名称	类型	是否必须	默认值	备注
file_id	string	是		
box	array	是		
contract_id	number	是		合同id
start_time	string	否		yyyy-mm-dd
end_time	string	否		yyyy-mm-dd
extract_type	number	否		识别类型 1-导入中 2-导入后 默认1

返回数据：
名称	类型	是否必须	默认值	备注
code	integer	是		
message	string	是		
data	object	是		
```
'''


class UTGenerator:
    """UT生成器：通过API文档构造UT"""

    def __init__(self, swagger_file: str, ut_py_path: str, questions_path: str,
                 chatgpt_method: str = "API", template_prefix=YFT_PROMPT_PREFIX) -> None:
        """初始化UT生成器

        Args:
            swagger_file: swagger路径
            ut_py_path: 用例存放路径
            questions_path: 模版存放路径，便于后续排查
            chatgpt_method: API
            template_prefix: 使用模版，默认使用YFT_UT_PROMPT
        """
        self.swagger_file = swagger_file
        self.ut_py_path = ut_py_path
        self.questions_path = questions_path
        assert chatgpt_method in ["API"], "非法chatgpt_method"
        self.chatgpt_method = chatgpt_method

        # ICL: In-Context Learning，这里给出例子，要求GPT模仿例子
        self.icl_sample = ICL_SAMPLE
        self.template_prefix = template_prefix

    def get_swagger_json(self) -> dict:
        """从本地文件加载Swagger JSON"""
        with open(self.swagger_file, "r", encoding="utf-8") as file:
            swagger_json = json.load(file)
        return swagger_json

    def __para_to_str(self, prop, required, name=""):
        name = name or prop["name"]
        ptype = prop["type"]
        title = prop.get("title", "")
        desc = prop.get("description", "")
        return f'{name}\t{ptype}\t{"是" if required else "否"}\t{title}\t{desc}'

    def _para_to_str(self, prop):
        required = prop.get("required", False)
        return self.__para_to_str(prop, required)

    def para_to_str(self, name, prop, prop_object_required):
        required = name in prop_object_required
        return self.__para_to_str(prop, required, name)

    def build_object_properties(self, node, prop_object_required, level: int = 0) -> str:
        """递归输出object和array[object]类型的子属性

        Args:
            node (_type_): 子项的值
            prop_object_required (_type_): 是否必填项
            level: 当前递归深度
        """

        doc = ""

        def dive_into_object(node):
            """如果是object类型，递归输出子属性"""
            if node.get("type") == "object":
                sub_properties = node.get("properties", {})
                return self.build_object_properties(sub_properties, prop_object_required, level=level + 1)
            return ""

        if node.get("in", "") in ["query", "header", "formData"]:
            doc += f'{"	" * level}{self._para_to_str(node)}\n'
            doc += dive_into_object(node)
            return doc

        for name, prop in node.items():
            doc += f'{"	" * level}{self.para_to_str(name, prop, prop_object_required)}\n'
            doc += dive_into_object(prop)
            if prop["type"] == "array":
                items = prop.get("items", {})
                doc += dive_into_object(items)
        return doc

    def get_tags_mapping(self) -> dict:
        """处理tag与path

        Returns:
            Dict: tag: path对应关系
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
        """生成用例文件"""
        tags = self.get_tags_mapping()
        for tag, paths in tags.items():
            if include_tags is None or tag in include_tags:
                self._generate_ut(tag, paths)
        return True

    def build_api_doc(self, node: dict, path: str, method: str) -> str:
        summary = node["summary"]

        doc = f"接口名称：{summary}\n接口路径：{path}\nMethod：{method.upper()}\n"
        doc += "\n请求参数：\n"
        if "parameters" in node:
            parameters = node["parameters"]
            doc += "路径参数：\n"

            # param["in"]: path / formData / body / query / header
            for param in parameters:
                if param["in"] == "path":
                    doc += f'{param["name"]} \n'

            doc += "\nBody参数：\n"
            doc += "名称\t类型\t是否必须\t默认值\t备注\n"
            for param in parameters:
                if param["in"] == "body":
                    schema = param.get("schema", {})
                    prop_properties = schema.get("properties", {})
                    prop_required = schema.get("required", [])
                    doc += self.build_object_properties(prop_properties, prop_required)
                else:
                    doc += self.build_object_properties(param, [])

        # 输出返回数据信息
        doc += "\n返回数据：\n"
        doc += "名称\t类型\t是否必须\t默认值\t备注\n"
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
        file_path = self.get_file_path(Path(base) / folder, fname)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(data)

    def ask_gpt_and_save(self, question: str, tag: str, fname: str):
        """生成问题，并且存储问题与答案"""
        messages = [self.icl_sample, question]
        result = self.gpt_msgs_to_code(messages=messages)

        self._store(question, self.questions_path, tag, f"{fname}.txt")
        self._store(result, self.ut_py_path, tag, f"{fname}.py")

    def _generate_ut(self, tag, paths):
        """处理数据路径下的结构

        Args:
            tag (_type_): 模块名称
            paths (_type_): 路径Object
        """
        for path, path_obj in paths.items():
            for method, node in path_obj.items():
                summary = node["summary"]
                question = self.template_prefix
                question += self.build_api_doc(node, path, method)
                self.ask_gpt_and_save(question, tag, summary)

    def gpt_msgs_to_code(self, messages: list) -> str:
        """根据不同调用方式选择"""
        result = ''
        if self.chatgpt_method == "API":
            result = GPTAPI().ask_code(msgs=messages)

        return result

    def get_file_path(self, base: Path, fname: str):
        """保存不同的文件路径

        Args:
            base (str): 路径
            fname (str): 文件名称
        """
        path = Path(base)
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / fname
        return str(file_path)
