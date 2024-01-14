#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 13:05
@Author  : alexanderwu
@File    : mock_markdown.py
"""
import json

from metagpt.actions import UserRequirement, WriteDesign, WritePRD, WriteTasks
from metagpt.schema import Message

USER_REQUIREMENT = """开发一个基于大语言模型与私有知识库的搜索引擎，希望可以基于大语言模型进行搜索总结"""

DETAIL_REQUIREMENT = """需求：开发一个基于LLM（大语言模型）与私有知识库的搜索引擎，希望有几点能力
1. 用户可以在私有知识库进行搜索，再根据大语言模型进行总结，输出的结果包括了总结
2. 私有知识库可以实时更新，底层基于 ElasticSearch
3. 私有知识库支持pdf、word、txt等各种文件格式上传，上传后可以在服务端解析为文本，存储ES

资源：
1. 大语言模型已经有前置的抽象、部署，可以通过 `from metagpt.llm import LLM`，再使用`LLM().ask(prompt)`直接调用
2. Elastic已有[部署](http://192.168.50.82:9200/)，代码可以直接使用这个部署"""


PRD = '''## 原始需求
```python
"""
我们希望开发一个基于大语言模型与私有知识库的搜索引擎。该搜索引擎应当能根据用户输入的查询进行智能搜索，并基于大语言模型对搜索结果进行总结，以便用户能够快速获取他们所需要的信息。该搜索引擎应当能够处理大规模的数据，同时保持搜索结果的准确性和相关性。我们希望这个产品能够降低用户在查找、筛选和理解信息时的工作负担，提高他们的工作效率。
"""
```

## 产品目标
```python
[
    "提供高准确性、高相关性的搜索结果，满足用户的查询需求",
    "基于大语言模型对搜索结果进行智能总结，帮助用户快速获取所需信息",
    "处理大规模数据，保证搜索的速度和效率，提高用户的工作效率"
]
```

## 用户故事
```python
[
    "假设用户是一名研究员，他正在为一项关于全球气候变化的报告做研究。他输入了'全球气候变化的最新研究'，我们的搜索引擎快速返回了相关的文章、报告、数据集等。并且基于大语言模型对这些信息进行了智能总结，研究员可以快速了解到最新的研究趋势和发现。",
    "用户是一名学生，正在为即将到来的历史考试复习。他输入了'二战的主要战役'，搜索引擎返回了相关的资料，大语言模型总结出主要战役的时间、地点、结果等关键信息，帮助学生快速记忆。",
    "用户是一名企业家，他正在寻找关于最新的市场趋势信息。他输入了'2023年人工智能市场趋势'，搜索引擎返回了各种报告、新闻和分析文章。大语言模型对这些信息进行了总结，用户能够快速了解到市场的最新动态和趋势。"
]
```

## 竞品分析
```python
[
    "Google Search：Google搜索是市场上最主要的搜索引擎，它能够提供海量的搜索结果。但Google搜索并不提供搜索结果的总结功能，用户需要自己去阅读和理解搜索结果。",
    "Microsoft Bing：Bing搜索也能提供丰富的搜索结果，同样没有提供搜索结果的总结功能。",
    "Wolfram Alpha：Wolfram Alpha是一个基于知识库的计算型搜索引擎，能够针对某些特定类型的查询提供直接的答案和总结，但它的知识库覆盖范围有限，无法处理大规模的数据。"
]
```

## 开发需求池
```python
[
    ("开发基于大语言模型的智能总结功能", 5),
    ("开发搜索引擎核心算法，包括索引构建、查询处理、结果排序等", 7),
    ("设计和实现用户界面，包括查询输入、搜索结果展示、总结结果展示等", 3),
    ("构建和维护私有知识库，包括数据采集、清洗、更新等", 7),
    ("优化搜索引擎性能，包括搜索速度、准确性、相关性等", 6),
    ("开发用户反馈机制，包括反馈界面、反馈处理等", 2),
    ("开发安全防护机制，防止恶意查询和攻击", 3),
    ("集成大语言模型，包括模型选择、优化、更新等", 5),
    ("进行大规模的测试，包括功能测试、性能测试、压力测试等", 5),
    ("开发数据监控和日志系统，用于监控搜索引擎的运行状态和性能", 4)
]
```
'''

SYSTEM_DESIGN = """## Project name
```python
"smart_search_engine"
```

## Task list:
```python
[
    "smart_search_engine/__init__.py",
    "smart_search_engine/main.py",
    "smart_search_engine/search.py",
    "smart_search_engine/index.py",
    "smart_search_engine/ranking.py",
    "smart_search_engine/summary.py",
    "smart_search_engine/knowledge_base.py",
    "smart_search_engine/interface.py",
    "smart_search_engine/user_feedback.py",
    "smart_search_engine/security.py",
    "smart_search_engine/testing.py",
    "smart_search_engine/monitoring.py"
]
```

## Data structures and interfaces
```mermaid
classDiagram
    class Main {
        -SearchEngine search_engine
        +main() str
    }
    class SearchEngine {
        -Index index
        -Ranking ranking
        -Summary summary
        +search(query: str) str
    }
    class Index {
        -KnowledgeBase knowledge_base
        +create_index(data: dict)
        +query_index(query: str) list
    }
    class Ranking {
        +rank_results(results: list) list
    }
    class Summary {
        +summarize_results(results: list) str
    }
    class KnowledgeBase {
        +update(data: dict)
        +fetch_data(query: str) dict
    }
    Main --> SearchEngine
    SearchEngine --> Index
    SearchEngine --> Ranking
    SearchEngine --> Summary
    Index --> KnowledgeBase
```

## Program call flow
```mermaid
sequenceDiagram
    participant M as Main
    participant SE as SearchEngine
    participant I as Index
    participant R as Ranking
    participant S as Summary
    participant KB as KnowledgeBase
    M->>SE: search(query)
    SE->>I: query_index(query)
    I->>KB: fetch_data(query)
    KB-->>I: return data
    I-->>SE: return results
    SE->>R: rank_results(results)
    R-->>SE: return ranked_results
    SE->>S: summarize_results(ranked_results)
    S-->>SE: return summary
    SE-->>M: return summary
```
"""

JSON_TASKS = {
    "Logic Analysis": """
    在这个项目中，所有的模块都依赖于“SearchEngine”类，这是主入口，其他的模块（Index、Ranking和Summary）都通过它交互。另外，"Index"类又依赖于"KnowledgeBase"类，因为它需要从知识库中获取数据。

- "main.py"包含"Main"类，是程序的入口点，它调用"SearchEngine"进行搜索操作，所以在其他任何模块之前，"SearchEngine"必须首先被定义。
- "search.py"定义了"SearchEngine"类，它依赖于"Index"、"Ranking"和"Summary"，因此，这些模块需要在"search.py"之前定义。
- "index.py"定义了"Index"类，它从"knowledge_base.py"获取数据来创建索引，所以"knowledge_base.py"需要在"index.py"之前定义。
- "ranking.py"和"summary.py"相对独立，只需确保在"search.py"之前定义。
- "knowledge_base.py"是独立的模块，可以优先开发。
- "interface.py"、"user_feedback.py"、"security.py"、"testing.py"和"monitoring.py"看起来像是功能辅助模块，可以在主要功能模块开发完成后并行开发。
    """,
    "Task list": [
        "smart_search_engine/knowledge_base.py",
        "smart_search_engine/index.py",
        "smart_search_engine/ranking.py",
        "smart_search_engine/summary.py",
        "smart_search_engine/search.py",
        "smart_search_engine/main.py",
        "smart_search_engine/interface.py",
        "smart_search_engine/user_feedback.py",
        "smart_search_engine/security.py",
        "smart_search_engine/testing.py",
        "smart_search_engine/monitoring.py",
    ],
}


TASKS = """## Logic Analysis

在这个项目中，所有的模块都依赖于“SearchEngine”类，这是主入口，其他的模块（Index、Ranking和Summary）都通过它交互。另外，"Index"类又依赖于"KnowledgeBase"类，因为它需要从知识库中获取数据。

- "main.py"包含"Main"类，是程序的入口点，它调用"SearchEngine"进行搜索操作，所以在其他任何模块之前，"SearchEngine"必须首先被定义。
- "search.py"定义了"SearchEngine"类，它依赖于"Index"、"Ranking"和"Summary"，因此，这些模块需要在"search.py"之前定义。
- "index.py"定义了"Index"类，它从"knowledge_base.py"获取数据来创建索引，所以"knowledge_base.py"需要在"index.py"之前定义。
- "ranking.py"和"summary.py"相对独立，只需确保在"search.py"之前定义。
- "knowledge_base.py"是独立的模块，可以优先开发。
- "interface.py"、"user_feedback.py"、"security.py"、"testing.py"和"monitoring.py"看起来像是功能辅助模块，可以在主要功能模块开发完成后并行开发。

## Task list

```python
task_list = [
    "smart_search_engine/knowledge_base.py",
    "smart_search_engine/index.py",
    "smart_search_engine/ranking.py",
    "smart_search_engine/summary.py",
    "smart_search_engine/search.py",
    "smart_search_engine/main.py",
    "smart_search_engine/interface.py",
    "smart_search_engine/user_feedback.py",
    "smart_search_engine/security.py",
    "smart_search_engine/testing.py",
    "smart_search_engine/monitoring.py",
]
```
这个任务列表首先定义了最基础的模块，然后是依赖这些模块的模块，最后是辅助模块。可以根据团队的能力和资源，同时开发多个任务，只要满足依赖关系。例如，在开发"search.py"之前，可以同时开发"knowledge_base.py"、"index.py"、"ranking.py"和"summary.py"。
"""


TASKS_TOMATO_CLOCK = '''## Required Python third-party packages: Provided in requirements.txt format
```python
Flask==2.1.1
Jinja2==3.1.0
Bootstrap==5.3.0-alpha1
```

## Logic Analysis: Provided as a Python str, analyze the dependencies between the files, which work should be done first
```python
"""
1. Start by setting up the Flask app, config.py, and requirements.txt to create the basic structure of the web application.
2. Create the timer functionality using JavaScript and the Web Audio API in the timer.js file.
3. Develop the frontend templates (index.html and settings.html) using Jinja2 and integrate the timer functionality.
4. Add the necessary static files (main.css, main.js, and notification.mp3) for styling and interactivity.
5. Implement the ProgressBar class in main.js and integrate it with the Timer class in timer.js.
6. Write tests for the application in test_app.py.
"""
```

## Task list: Provided as Python list[str], each str is a file, the more at the beginning, the more it is a prerequisite dependency, should be done first
```python
task_list = [
    'app.py',
    'config.py',
    'requirements.txt',
    'static/js/timer.js',
    'templates/index.html',
    'templates/settings.html',
    'static/css/main.css',
    'static/js/main.js',
    'static/audio/notification.mp3',
    'static/js/progressbar.js',
    'tests/test_app.py'
]
```
'''

TASK = """smart_search_engine/knowledge_base.py"""

STRS_FOR_PARSING = [
    """
## 1
```python
a
```
""",
    """
##2
```python
"a"
```
""",
    """
##  3
```python
a = "a"
```
""",
    """
## 4
```python
a =  'a'
```
""",
]


class MockMessages:
    req = Message(role="User", content=USER_REQUIREMENT, cause_by=UserRequirement)
    prd = Message(role="Product Manager", content=PRD, cause_by=WritePRD)
    system_design = Message(role="Architect", content=SYSTEM_DESIGN, cause_by=WriteDesign)
    tasks = Message(role="Project Manager", content=TASKS, cause_by=WriteTasks)
    json_tasks = Message(
        role="Project Manager", content=json.dumps(JSON_TASKS, ensure_ascii=False), cause_by=WriteTasks
    )
