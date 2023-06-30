# MetaGPT：多角色元编程框架

[English](./README.md) / [中文](./README_CN.md)

## 目标

1. 我们的最终目标是让 GPT 能够训练、微调，并最终利用自身，以实现**自我进化**
   1. 一旦 GPT 能够优化自身，它将有能力持续改进自己的性能，而无需经常手动调整。这种自我进化使得 AI 能够识别自身改进的领域，进行必要的调整，并实施那些改变以更好地达到其目标。**这可能导致系统能力的指数级增长**
2. 目前，我们已经使 GPT 能够以团队的形式工作，协作处理更复杂的任务
   1. 例如，`startup.py` 包括**产品经理 / 架构师 / 项目经理 / 工程师**，它提供了一个**软件公司**的全过程
   2. 该团队可以合作并生成**用户故事 / 竞品分析 / 需求 / 数据结构 / APIs / 文件等**

### 哲学

软件公司核心资产有三：可运行的代码，SOP，团队。有公式：

```
可运行的代码 = SOP(团队)
```

我们践行了这个过程，并且将SOP以代码形式表达了出来，而团队本身仅使用了大模型

## 示例（均由 GPT-4 生成）

1. 这里的每一列都是使用命令 `python startup.py <requirement>` 的要求
2. 默认情况下，每个示例的投资为三美元，一旦这个金额耗尽，程序就会停止
   1. 生成一个带有分析和设计的示例大约需要**$0.2** (GPT-4 api 的费用)
   2. 生成一个完整项目的示例大约需要**$2.0** (GPT-4 api 的费用)

|             | 设计一个支持 GPT-4 和其他 LLMs 的 MLOps/LLMOps 框架                                                   | 设计一个像 Candy Crush Saga 的游戏                                                                       | 设计一个像今日头条的 RecSys                                                                             | 设计一个像 NetHack 的 roguelike 游戏                                                        | 设计一个搜索算法框架                                                                                         | 设计一个简约的番茄钟计时器                                                                                       |
|-------------|-------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| 竞品分析        | ![LLMOps 竞品分析](resources/workspace/llmops_framework/resources/competitive_analysis.png)   | ![Candy Crush 竞品分析](resources/workspace/match3_puzzle_game/resources/competitive_analysis.png)   | ![今日头条 Recsys 竞品分析](resources/workspace/content_rec_sys/resources/competitive_analysis.png)   | ![NetHack 游戏竞品分析](resources/workspace/pyrogue/resources/competitive_analysis.png)   | ![搜索算法框架竞品分析](resources/workspace/search_algorithm_framework/resources/competitive_analysis.png)   | ![简约番茄钟计时器竞品分析](resources/workspace/minimalist_pomodoro_timer/resources/competitive_analysis.png)   |
| 数据 & API 设计 | ![LLMOps 数据 & API 设计](resources/workspace/llmops_framework/resources/data_api_design.png) | ![Candy Crush 数据 & API 设计](resources/workspace/match3_puzzle_game/resources/data_api_design.png) | ![今日头条 Recsys 数据 & API 设计](resources/workspace/content_rec_sys/resources/data_api_design.png) | ![NetHack 游戏数据 & API 设计](resources/workspace/pyrogue/resources/data_api_design.png) | ![搜索算法框架数据 & API 设计](resources/workspace/search_algorithm_framework/resources/data_api_design.png) | ![简约番茄钟计时器数据 & API 设计](resources/workspace/minimalist_pomodoro_timer/resources/data_api_design.png) |
| 序列流程图       | ![LLMOps 序列流程图](resources/workspace/llmops_framework/resources/seq_flow.png)              | ![Candy Crush 序列流程图](resources/workspace/match3_puzzle_game/resources/seq_flow.png)              | ![今日头条 Recsys 序列流程图](resources/workspace/content_rec_sys/resources/seq_flow.png)              | ![NetHack 游戏序列流程图](resources/workspace/pyrogue/resources/seq_flow.png)              | ![搜索算法框架序列流程图](resources/workspace/search_algorithm_framework/resources/seq_flow.png)              | ![简约番茄钟计时器序列流程图](resources/workspace/minimalist_pomodoro_timer/resources/seq_flow.png)              |

## 安装

```bash
# 第 1 步：确保您的系统上安装了 Python 3.9+。您可以使用以下命令进行检查：
python --version

# 第 2 步：确保您的系统上安装了 NPM。您可以使用以下命令进行检查：
npm --version

# 第 3 步：克隆仓库到您的本地机器，并进行安装。
git clone https://github.com/geekan/metagpt
cd metagpt
python setup.py install
```

## 配置

- 您可以在 `config/key.yaml / config/config.yaml / env` 中配置您的 `OPENAI_API_KEY`
- 优先级顺序：`config/key.yaml > config/config.yaml > env`

```bash
# 复制配置文件并进行必要的修改。
cp config/config.yaml config/key.yaml
```

| 变量名                              | config/key.yaml                           | env                            |
|--------------------------------------------|-------------------------------------------|--------------------------------|
| OPENAI_API_KEY # 用您自己的密钥替换 | OPENAI_API_KEY: "sk-..."                  | export OPENAI_API_KEY="sk-..." |
| OPENAI_API_BASE # 可选  | OPENAI_API_BASE: "https://<YOUR_SITE>/v1" | export OPENAI_API_BASE="https://<YOUR_SITE>/v1"   |

## 示例：启动一个创业公司

```shell
python startup.py "写一个命令行贪吃蛇"
```

运行脚本后，您可以在 `workspace/` 目录中找到您的新项目。

### 背后的运作原理？这是一个完全由 GPT 驱动的创业公司，而您是投资者

| 一个完全由大语言模型角色构成的软件公司（仅示例）                                     | 一个软件公司的SOP可视化（仅示例）                                                |
|--------------------------------------------------------------|-------------------------------------------------------------------|
| ![一个完全由大语言模型角色构成的软件公司](./resources/software_company_cd.jpeg) | ![A software company's SOP](./resources/software_company_sd.jpeg) |


### 代码实现

```python
from metagpt.software_company import SoftwareCompany
from metagpt.roles import ProjectManager, ProductManager, Architect, Engineer

async def startup(idea: str, investment: str = '$3.0', n_round: int = 5):
    """运行一个创业公司。做一个老板"""
    company = SoftwareCompany()
    company.hire([ProductManager(), Architect(), ProjectManager(), Engineer()])
    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)
```

## 示例：单角色能力与底层LLM调用

### 框架同样支持单角色能力，以下是一个销售角色（完整示例见examples）

```python
from metagpt.const import DATA_PATH
from metagpt.document_store import FaissStore
from metagpt.roles import Sales

store = FaissStore(DATA_PATH / 'example.pdf')
role = Sales(profile='Sales', store=store)
result = await role.run('Which facial cleanser is good for oily skin?')
```

### 框架也支持LLM的直接接口

```python
from metagpt.llm import LLM

llm = LLM()
await llm.aask('hello world')

hello_msg = [{'role': 'user', 'content': 'hello'}]
await llm.acompletion(hello_msg)
```

## 联系信息

如果您对这个项目有任何问题或反馈，欢迎联系我们。我们非常欢迎您的建议！

- **邮箱：** alexanderwu@fuzhi.ai
- **GitHub 问题：** 对于更技术性的问题，您也可以在我们的 [GitHub 仓库](https://github.com/geekan/metagpt/issues) 中创建一个新的问题。

我们会在2-3个工作日内回复所有的查询。
