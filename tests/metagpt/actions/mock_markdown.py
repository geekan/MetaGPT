#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/18 23:51
@Author  : alexanderwu
@File    : mock_markdown.py
"""

PRD_SAMPLE = """## Original Requirements
The original requirement is to create a game similar to the classic text-based adventure game, Zork.

## Product Goals
```python
product_goals = [
    "Create an engaging text-based adventure game",
    "Ensure the game is easy to navigate and user-friendly",
    "Incorporate compelling storytelling and puzzles"
]
```

## User Stories
```python
user_stories = [
    "As a player, I want to be able to easily input commands so that I can interact with the game world",
    "As a player, I want to explore various rooms and locations to uncover the game's story",
    "As a player, I want to solve puzzles to progress in the game",
    "As a player, I want to interact with various in-game objects to enhance my gameplay experience",
    "As a player, I want a game that challenges my problem-solving skills and keeps me engaged"
]
```

## Competitive Analysis
```python
competitive_analysis = [
    "Zork: The original text-based adventure game with complex puzzles and engaging storytelling",
    "The Hitchhiker's Guide to the Galaxy: A text-based game with a unique sense of humor and challenging gameplay",
    "Colossal Cave Adventure: The first text adventure game which set the standard for the genre",
    "Quest: A platform that lets users create their own text adventure games",
    "ChatGPT: An AI that can generate text-based adventure games",
    "The Forest of Doom: A text-based game with a fantasy setting and multiple endings",
    "Wizards Choice: A text-based game with RPG elements and a focus on player choice"
]
```

## Competitive Quadrant Chart
```mermaid
quadrantChart
    title Reach and engagement of text-based adventure games
    x-axis Low Reach --> High Reach
    y-axis Low Engagement --> High Engagement
    quadrant-1 High potential games
    quadrant-2 Popular but less engaging games
    quadrant-3 Less popular and less engaging games
    quadrant-4 Popular and engaging games
    "Zork": [0.9, 0.8]
    "Hitchhiker's Guide": [0.7, 0.7]
    "Colossal Cave Adventure": [0.8, 0.6]
    "Quest": [0.4, 0.5]
    "ChatGPT": [0.3, 0.6]
    "Forest of Doom": [0.5, 0.4]
    "Wizards Choice": [0.6, 0.5]
    "Our Target Product": [0.5, 0.6]
```

## Requirement Analysis
The goal is to create a text-based adventure game similar to Zork. The game should be engaging, user-friendly, and feature compelling storytelling and puzzles. It should allow players to explore various rooms and locations, interact with in-game objects, and solve puzzles to progress. The game should also challenge players' problem-solving skills and keep them engaged.

## Requirement Pool
```python
requirement_pool = [
    ("Design an intuitive command input system for player interactions", "P0"),
    ("Create a variety of rooms and locations for players to explore", "P0"),
    ("Develop engaging puzzles that players need to solve to progress", "P0"),
    ("Incorporate a compelling story that unfolds as players explore the game world", "P1"),
    ("Ensure the game is user-friendly and easy to navigate", "P1")
]
```

## Anything UNCLEAR
The original requirement did not specify the platform for the game (web, mobile, desktop) or any specific features or themes for the game's story and puzzles. More information on these aspects could help in further refining the product requirements and design.
"""

DESIGN_LLM_KB_SEARCH_SAMPLE = """## Implementation approach:

The game will be developed as a console application in Python, which will allow it to be platform-independent. The game logic will be implemented using Object Oriented Programming principles. 

The game will consist of different "rooms" or "locations" that the player can navigate. Each room will have different objects and puzzles that the player can interact with. The player's progress in the game will be determined by their ability to solve these puzzles.

Python's in-built data structures like lists and dictionaries will be used extensively to manage the game state, player inventory, room details, etc. 

For testing, we can use the PyTest framework. This is a mature full-featured Python testing tool that helps you write better programs.

## Project Name:
```python
"adventure_game"
```

## File list:
```python
file_list = ["main.py", "room.py", "player.py", "game.py", "object.py", "puzzle.py", "test_game.py"]
```

## Data structures and interfaces:
```mermaid
classDiagram
    class Room{
        +__init__(self, description: str, objects: List[Object])
        +get_description(self) -> str
        +get_objects(self) -> List[Object]
    }
    class Player{
        +__init__(self, current_room: Room, inventory: List[Object])
        +move(self, direction: str) -> None
        +get_current_room(self) -> Room
        +get_inventory(self) -> List[Object]
    }
    class Object{
        +__init__(self, name: str, description: str, is_usable: bool)
        +get_name(self) -> str
        +get_description(self) -> str
        +is_usable(self) -> bool
    }
    class Puzzle{
        +__init__(self, question: str, answer: str, reward: Object)
        +ask_question(self) -> str
        +check_answer(self, player_answer: str) -> bool
        +get_reward(self) -> Object
    }
    class Game{
        +__init__(self, player: Player)
        +start(self) -> None
        +end(self) -> None
    }
    Room "1" -- "*" Object
    Player "1" -- "1" Room
    Player "1" -- "*" Object
    Puzzle "1" -- "1" Object
    Game "1" -- "1" Player
```

## Program call flow:
```mermaid
sequenceDiagram
    participant main as main.py
    participant Game as Game
    participant Player as Player
    participant Room as Room
    main->>Game: Game(player)
    Game->>Player: Player(current_room, inventory)
    Player->>Room: Room(description, objects)
    Game->>Game: start()
    Game->>Player: move(direction)
    Player->>Room: get_description()
    Game->>Player: get_inventory()
    Game->>Game: end()
```

## Anything UNCLEAR:
The original requirements did not specify whether the game should have a save/load feature, multiplayer support, or any specific graphical user interface. More information on these aspects could help in further refining the product design and requirements.
"""


PROJECT_MANAGEMENT_SAMPLE = '''## Required Python third-party packages: Provided in requirements.txt format
```python
"pytest==6.2.5"
```

## Required Other language third-party packages: Provided in requirements.txt format
```python
```

## Full API spec: Use OpenAPI 3.0. Describe all APIs that may be used by both frontend and backend.
```python
"""
This project is a console-based application and doesn't require any API endpoints. All interactions will be done through the console interface.
"""
```

## Logic Analysis: Provided as a Python list[str, str]. the first is filename, the second is class/method/function should be implemented in this file. Analyze the dependencies between the files, which work should be done first
```python
[
    ("object.py", "Object"),
    ("room.py", "Room"),
    ("player.py", "Player"),
    ("puzzle.py", "Puzzle"),
    ("game.py", "Game"),
    ("main.py", "main"),
    ("test_game.py", "test_game")
]
```

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first
```python
[
    "object.py", 
    "room.py", 
    "player.py", 
    "puzzle.py", 
    "game.py", 
    "main.py", 
    "test_game.py"
]
```

## Shared Knowledge: Anything that should be public like utils' functions, config's variables details that should make clear first. 
```python
"""
Shared knowledge for this project includes understanding the basic principles of Object Oriented Programming, Python's built-in data structures like lists and dictionaries, and the PyTest framework for testing. 
"""
```

## Anything UNCLEAR: Provide as Plain text. Try to clarify it. For example, don't forget a main entry. don't forget to init 3rd party libs.
```python
"""
The original requirements did not specify whether the game should have a save/load feature, multiplayer support, or any specific graphical user interface. More information on these aspects could help in further refining the product design and requirements.
"""
```
'''


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
    "智能推荐API：根据用户的搜索历史记录和搜索行为，推荐相关的搜索结果。",
]

TASKS_2 = ["完成main.py的功能"]

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

MEILI_CODE = """import meilisearch
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
"""

MEILI_ERROR = """/usr/local/bin/python3.9 /Users/alexanderwu/git/metagpt/examples/search/meilisearch_index.py
Traceback (most recent call last):
  File "/Users/alexanderwu/git/metagpt/examples/search/meilisearch_index.py", line 44, in <module>
    search_engine.add_documents(books_data_source, documents)
  File "/Users/alexanderwu/git/metagpt/examples/search/meilisearch_index.py", line 25, in add_documents
    index = self.client.get_or_create_index(index_name)
AttributeError: 'Client' object has no attribute 'get_or_create_index'

Process finished with exit code 1"""

MEILI_CODE_REFINED = """
"""
