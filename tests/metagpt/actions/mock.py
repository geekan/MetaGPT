#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/18 23:51
@Author  : alexanderwu
@File    : mock.py
"""

PRD_SAMPLE = """产品/功能介绍：基于大语言模型的、私有知识库的搜索引擎

目标：实现一个高效、准确、易用的搜索引擎，能够满足用户对私有知识库的搜索需求，提高工作效率和信息检索的准确性。

用户和使用场景：该搜索引擎主要面向需要频繁使用私有知识库进行信息检索的用户，例如企业内部的知识管理者、研发人员和数据分析师等。用户需要通过输入关键词或短语，快速地获取与其相关的知识库内容。

需求：
1. 支持基于大语言模型的搜索算法，能够对用户输入的关键词或短语进行语义理解，提高搜索结果的准确性。
2. 支持私有知识库的建立和维护，能够对知识库内容进行分类、标签和关键词的管理，方便用户进行信息检索。
3. 提供简洁、直观的用户界面，支持多种搜索方式（如全文搜索、精确搜索、模糊搜索等），方便用户进行快速检索。
4. 支持搜索结果的排序和过滤，能够根据相关度、时间等因素对搜索结果进行排序，方便用户找到最相关的信息。
5. 支持多种数据格式的导入和导出，方便用户对知识库内容进行备份和分享。

约束与限制：由于资源有限，需要在保证产品质量的前提下，控制开发成本和时间。同时，需要考虑用户的隐私保护和知识库内容的安全性。

性能指标：
1. 搜索响应时间：搜索引擎的搜索响应时间应该在毫秒级别，能够快速响应用户的搜索请求。
2. 搜索准确率：搜索引擎应该能够准确地返回与用户搜索意图相关的知识库内容，提高搜索结果的准确率。
3. 系统稳定性：搜索引擎应该具备良好的稳定性和可靠性，能够在高并发、大数据量等情况下保持正常运行。
4. 用户体验：搜索引擎的用户界面应该简洁、直观、易用，让用户能够快速地找到所需的信息。
"""

DESIGN_LLM_KB_SEARCH_SAMPLE = """## 数据结构
- 文档对象(Document Object)：表示知识库中的一篇文档，包含文档的标题、内容、标签等信息。
- 知识库对象(Knowledge Base Object)：表示整个知识库，包含多篇文档对象，以及知识库的分类、标签等信息。

## API接口
- create_document(title, content, tags)：创建一篇新的文档，返回文档对象。
- delete_document(document_id)：删除指定ID的文档。
- update_document(document_id, title=None, content=None, tags=None)：更新指定ID的文档的标题、内容、标签等信息。
- search_documents(query, mode='fulltext', limit=10, sort_by='relevance')：根据查询条件进行搜索，返回符合条件的文档列表。
- create_knowledge_base(name, description=None)：创建一个新的知识库，返回知识库对象。
- delete_knowledge_base(kb_id)：删除指定ID的知识库。
- update_knowledge_base(kb_id, name=None, description=None)：更新指定ID的知识库的名称、描述等信息。

## 调用流程（以dot语言描述）
```dot
digraph search_engine {
  User -> UI [label="1. 输入查询关键词"];
  UI -> API [label="2. 调用搜索API"];
  API -> KnowledgeBase [label="3. 查询知识库"];
  KnowledgeBase -> NLP [label="4. 进行自然语言处理"];
  NLP -> API [label="5. 返回处理结果"];
  API -> UI [label="6. 返回搜索结果"];
  UI -> User [label="7. 显示搜索结果"];
}
```

## 用户编写程序所需的全部、详尽的文件路径列表（以python字符串描述）
- /api/main.py：主程序入口
- /api/models/document.py：文档对象的定义
- /api/models/knowledge_base.py：知识库对象的定义
- /api/api/search_api.py：搜索API的实现
- /api/api/knowledge_base_api.py：知识库API的实现
- /api/nlp/nlp_engine.py：自然语言处理引擎的实现
- /api/ui/search_ui.py：搜索界面的实现
- /api/ui/knowledge_base_ui.py：知识库界面的实现
- /api/utils/database.py：数据库连接和操作相关的工具函数
- /api/utils/config.py：配置文件，包含数据库连接信息等配置项。
"""


WRITE_CODE_PROMPT_SAMPLE = """
你是一个工程师。下面是背景信息与你的当前任务，请为任务撰写代码。
撰写的代码应该符合PEP8，优雅，模块化，易于阅读与维护，代码本身应该有__main__入口来防止桩函数

## 用户编写程序所需的全部、详尽的文件路径列表（只需要相对路径，并不需要前缀，组织形式应该符合PEP规范）

- `main.py`: 主程序文件
- `search_engine.py`: 搜索引擎实现文件
- `knowledge_base.py`: 知识库管理文件
- `user_interface.py`: 用户界面文件
- `data_import.py`: 数据导入功能文件
- `data_export.py`: 数据导出功能文件
- `utils.py`: 工具函数文件

## 数据结构

- `KnowledgeBase`: 知识库类，用于管理私有知识库的内容、分类、标签和关键词。
- `SearchEngine`: 搜索引擎类，基于大语言模型，用于对用户输入的关键词或短语进行语义理解，并提供准确的搜索结果。
- `SearchResult`: 搜索结果类，包含与用户搜索意图相关的知识库内容的相关信息。
- `UserInterface`: 用户界面类，提供简洁、直观的用户界面，支持多种搜索方式和搜索结果的排序和过滤。
- `DataImporter`: 数据导入类，支持多种数据格式的导入功能，用于将外部数据导入到知识库中。
- `DataExporter`: 数据导出类，支持多种数据格式的导出功能，用于将知识库内容进行备份和分享。

## API接口

- `KnowledgeBase`类接口:
  - `add_entry(entry: str, category: str, tags: List[str], keywords: List[str]) -> bool`: 添加知识库条目。
  - `delete_entry(entry_id: str) -> bool`: 删除知识库条目。
  - `update_entry(entry_id: str, entry: str, category: str, tags: List[str], keywords: List[str]) -> bool`: 更新知识库条目。
  - `search_entries(query: str) -> List[str]`: 根据查询词搜索知识库条目。

- `SearchEngine`类接口:
  - `search(query: str) -> SearchResult`: 根据用户查询词进行搜索，返回与查询意图相关的搜索结果。

- `UserInterface`类接口:
  - `display_search_results(results: List[SearchResult]) -> None`: 显示搜索结果。
  - `filter_results(results: List[SearchResult], filters: Dict[str, Any]) -> List[SearchResult]`: 根据过滤条件对搜索结果进行过滤。
  - `sort_results(results: List[SearchResult], key: str, reverse: bool = False) -> List[SearchResult]`: 根据指定的键对搜索结果进行排序。

- `DataImporter`类接口:
  - `import_data(file_path: str) -> bool`: 导入外部数据到知识库。

- `DataExporter`类接口:
  - `export_data(file_path: str) -> bool`: 导出知识库数据到外部文件。

## 调用流程（以dot语言描述）

```dot
digraph call_flow {
    rankdir=LR;

    subgraph cluster_user_program {
        label="User Program";
        style=dotted;

        main_py -> search_engine_py;
        main_py -> knowledge_base_py;
        main_py -> user_interface_py;
        main_py -> data_import_py;
        main_py -> data_export_py;

        search_engine_py -> knowledge_base_py;
        search_engine_py -> user_interface_py;

        user_interface_py -> knowledge_base_py;
        user_interface_py -> search_engine_py;

        data_import_py -> knowledge_base_py;
        data_import_py -> user_interface_py;

        data_export_py -> knowledge_base_py;
        data_export_py -> user_interface_py;
    }

    main_py [label="main.py"];
    search_engine_py [label="search_engine.py"];
    knowledge_base_py [label="knowledge_base.py"];
    user_interface_py [label="user_interface.py"];
    data_import_py [label="data_import.py"];
    data_export_py [label="data_export.py"];
}
```

这是一个简化的调用流程图，展示了各个模块之间的调用关系。用户程序的`main.py`文件通过调用其他模块实现搜索引擎的功能。`search_engine.py`模块与`knowledge_base.py`和`user_interface.py`模块进行交互，实现搜索算法和搜索结果的展示。`data_import.py`和`data_export.py`模块与`knowledge_base.py`和`user_interface.py`模块进行交互，实现数据导入和导出的功能。用户界面模块`user_interface.py`与其他模块进行交互，提供简洁、直观的用户界面，并支持搜索方式、排序和过滤等操作。

## 当前任务

"""

TASKS = [
    "添加数据API：接受用户输入的文档库，对文档库进行索引\n- 使用MeiliSearch连接并添加文档库",
    "搜索API：接收用户输入的关键词，返回相关的搜索结果\n- 使用MeiliSearch连接并使用接口获得对应数据",
    "多条件筛选API：接收用户选择的筛选条件，返回符合条件的搜索结果。\n- 使用MeiliSearch进行筛选并返回符合条件的搜索结果",
    "智能推荐API：根据用户的搜索历史记录和搜索行为，推荐相关的搜索结果。"
]

TASKS_2 = [
    "完成main.py的功能"
]

SEARCH_CODE_SAMPLE = """
import requests


class SearchAPI:
    def __init__(self, elastic_search_url):
        self.elastic_search_url = elastic_search_url

    def search(self, keyword):
        # 构建搜索请求的参数
        params = {
            'q': keyword,
            'size': 10  # 返回结果数量
        }

        try:
            # 发送搜索请求
            response = requests.get(self.elastic_search_url, params=params)
            if response.status_code == 200:
                # 解析搜索结果
                search_results = response.json()
                formatted_results = self.format_results(search_results)
                return formatted_results
            else:
                print('Error: Failed to retrieve search results.')
        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')

    def format_results(self, search_results):
        formatted_results = []
        hits = search_results.get('hits', {}).get('hits', [])
        for hit in hits:
            result = hit.get('_source', {})
            title = result.get('title', '')
            summary = result.get('summary', '')
            url = result.get('url', '')
            formatted_results.append({
                'title': title,
                'summary': summary,
                'url': url
            })
        return formatted_results


if __name__ == '__main__':
    # 使用示例
    elastic_search_url = 'http://localhost:9200/search'
    search_api = SearchAPI(elastic_search_url)
    keyword = input('Enter search keyword: ')
    results = search_api.search(keyword)
    if results:
        for result in results:
            print(result)
    else:
        print('No results found.')
"""


REFINED_CODE = '''
import requests


class SearchAPI:
    def __init__(self, elastic_search_url):
        """
        初始化SearchAPI对象。

        Args:
            elastic_search_url (str): ElasticSearch的URL。
        """
        self.elastic_search_url = elastic_search_url

    def search(self, keyword, size=10):
        """
        搜索关键词并返回相关的搜索结果。

        Args:
            keyword (str): 用户输入的搜索关键词。
            size (int): 返回结果数量，默认为10。

        Returns:
            list: 包含搜索结果的列表，每个结果是一个字典，包含标题、摘要和URL等信息。如果没有搜索结果，返回一个空列表。
        """
        # 构建搜索请求的参数
        params = {
            'q': keyword,
            'size': size
        }

        try:
            # 发送搜索请求
            response = requests.get(self.elastic_search_url, params=params)
            response.raise_for_status()
            # 解析搜索结果
            search_results = response.json()
            formatted_results = self.format_results(search_results)
            return formatted_results
        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')
            return None

    def format_results(self, search_results):
        """
        格式化搜索结果。

        Args:
            search_results (dict): ElasticSearch返回的搜索结果。

        Returns:
            list: 包含格式化搜索结果的列表，每个结果是一个字典，包含标题、摘要和URL等信息。如果搜索结果为空，返回None。
        """
        if not isinstance(search_results, dict):
            return None

        formatted_results = []
        hits = search_results.get('hits', {}).get('hits', [])
        for hit in hits:
            result = hit.get('_source', {})
            title = result.get('title', '')
            summary = result.get('summary', '')
            url = result.get('url', '')
            formatted_results.append({
                'title': title,
                'summary': summary,
                'url': url
            })
        return formatted_results if formatted_results else None


if __name__ == '__main__':
    # 使用示例
    elastic_search_url = 'http://localhost:9200/search'
    search_api = SearchAPI(elastic_search_url)
    keyword = input('Enter search keyword: ')
    results = search_api.search(keyword)
    if results:
        for result in results:
            print(result)
    else:
        print('No results found.')
'''

MEILI_CODE = '''import meilisearch
from typing import List


class DataSource:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url


class SearchEngine:
    def __init__(self):
        self.client = meilisearch.Client('http://localhost:7700')  # MeiliSearch服务器的URL

    def add_documents(self, data_source: DataSource, documents: List[dict]):
        index_name = f"{data_source.name}_index"
        index = self.client.get_or_create_index(index_name)
        index.add_documents(documents)


# 示例用法
if __name__ == '__main__':
    search_engine = SearchEngine()

    # 假设有一个名为"books"的数据源，包含要添加的文档库
    books_data_source = DataSource(name='books', url='https://example.com/books')

    # 假设有一个名为"documents"的文档库，包含要添加的文档
    documents = [
        {"id": 1, "title": "Book 1", "content": "This is the content of Book 1."},
        {"id": 2, "title": "Book 2", "content": "This is the content of Book 2."},
        # 其他文档...
    ]

    # 添加文档库到搜索引擎
    search_engine.add_documents(books_data_source, documents)
'''

MEILI_ERROR = '''/usr/local/bin/python3.9 /Users/alexanderwu/git/metagpt/examples/search/meilisearch_index.py
Traceback (most recent call last):
  File "/Users/alexanderwu/git/metagpt/examples/search/meilisearch_index.py", line 44, in <module>
    search_engine.add_documents(books_data_source, documents)
  File "/Users/alexanderwu/git/metagpt/examples/search/meilisearch_index.py", line 25, in add_documents
    index = self.client.get_or_create_index(index_name)
AttributeError: 'Client' object has no attribute 'get_or_create_index'

Process finished with exit code 1'''

MEILI_CODE_REFINED = """
"""

