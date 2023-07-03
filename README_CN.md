# MetaGPT：多角色元编程框架

[English](./README.md) / [中文](./README_CN.md)

[![Discord Follow](https://dcbadge.vercel.app/api/server/wCp6Q3fsAk?compact=true&style=flat)](https://discord.gg/wCp6Q3fsAk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

使 GPT 以软件公司的形式工作，协作处理更复杂的任务

1. 该团队可以消化**一句话的老板需求**合作并生成**用户故事 / 竞品分析 / 需求 / 数据结构 / APIs / 文件等**
2. 该团队包括**产品经理 / 架构师 / 项目经理 / 工程师**，它提供了一个**软件公司**的全过程

![一个完全由大语言模型角色构成的软件公司](./resources/software_company_cd.jpeg)

## 示例（均由 GPT-4 生成）

例如，键入`python startup.py "写个类似今日头条的推荐系统"`并回车，你会获得一系列输出，其一是数据结构与API设计

![今日头条 Recsys 数据 & API 设计](resources/workspace/content_rec_sys/resources/data_api_design.png)

这需要大约**0.2美元**（GPT-4 API的费用）来生成一个带有分析和设计的示例，大约2.0美元用于一个完整的项目

## 安装

```bash
# 第 1 步：确保您的系统上安装了 NPM。并使用npm安装mermaid-js
npm --version
sudo npm install -g @mermaid-js/mermaid-cli

# 第 2 步：确保您的系统上安装了 Python 3.9+。您可以使用以下命令进行检查：
python --version

# 第 3 步：克隆仓库到您的本地机器，并进行安装。
git clone https://github.com/geekan/metagpt
cd metagpt
python setup.py install
```

## 配置

- 在 `config/key.yaml / config/config.yaml / env` 中配置您的 `OPENAI_API_KEY`
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

你可以查看`examples`，其中有单角色（带知识库）的使用例子与仅LLM的使用例子。

## 联系信息

如果您对这个项目有任何问题或反馈，欢迎联系我们。我们非常欢迎您的建议！

- **邮箱：** alexanderwu@fuzhi.ai
- **GitHub 问题：** 对于更技术性的问题，您也可以在我们的 [GitHub 仓库](https://github.com/geekan/metagpt/issues) 中创建一个新的问题。

我们会在2-3个工作日内回复所有的查询。

## 演示

https://github.com/geekan/MetaGPT/assets/2707039/5e8c1062-8c35-440f-bb20-2b0320f8d27d

## 加入微信讨论群

[//]: # (![MetaGPT WeChat Discuss Group]&#40;./resources/MetaGPT-WeChat-Group.jpeg&#41;{:height="50%" width="50%"})
<img src="./resources/MetaGPT-WeChat-Group-Simple.png" width = "30%" height = "30%" alt="MetaGPT WeChat Discuss Group" align=center />

