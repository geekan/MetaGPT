
# MetaGPT: The Multi-Agent Framework

<p align="center">
<a href=""><img src="docs/resources/MetaGPT-new-log.png" alt="MetaGPT logo: Enable GPT to work in software company, collaborating to tackle more complex tasks." width="150px"></a>
</p>

<p align="center">
<b>Assign different roles to GPTs to form a collaborative entity for complex tasks.</b>
</p>

<p align="center">
<a href="docs/README_CN.md"><img src="https://img.shields.io/badge/文档-中文版-blue.svg" alt="CN doc"></a>
<a href="README.md"><img src="https://img.shields.io/badge/document-English-blue.svg" alt="EN doc"></a>
<a href="docs/README_JA.md"><img src="https://img.shields.io/badge/ドキュメント-日本語-blue.svg" alt="JA doc"></a>
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
<a href="docs/ROADMAP.md"><img src="https://img.shields.io/badge/ROADMAP-路线图-blue" alt="roadmap"></a>
<a href="https://discord.gg/DYn29wFk9z"><img src="https://dcbadge.vercel.app/api/server/DYn29wFk9z?style=flat" alt="Discord Follow"></a>
<a href="https://twitter.com/MetaGPT_"><img src="https://img.shields.io/twitter/follow/MetaGPT?style=social" alt="Twitter Follow"></a>
</p>

<p align="center">
   <a href="https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/geekan/MetaGPT"><img src="https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode" alt="Open in Dev Containers"></a>
   <a href="https://codespaces.new/geekan/MetaGPT"><img src="https://img.shields.io/badge/Github_Codespace-Open-blue?logo=github" alt="Open in GitHub Codespaces"></a>
   <a href="https://huggingface.co/spaces/deepwisdom/MetaGPT" target="_blank"><img alt="Hugging Face" src="https://img.shields.io/badge/%F0%9F%A4%97%20-Hugging%20Face-blue?color=blue&logoColor=white" /></a>
</p>

## News
🚀 Mar. 29, 2024: [v0.8.0](https://github.com/geekan/MetaGPT/releases/tag/v0.8.0) released. Now you can use Data Interpreter via pypi package import. Meanwhile, we integrated RAG module and supported multiple new LLMs.

🚀 Mar. 14, 2024: Our **Data Interpreter** paper is on [arxiv](https://arxiv.org/abs/2402.18679). Check the [example](https://docs.deepwisdom.ai/main/en/DataInterpreter/) and [code](https://github.com/geekan/MetaGPT/tree/main/examples/di)!

🚀 Feb. 08, 2024: [v0.7.0](https://github.com/geekan/MetaGPT/releases/tag/v0.7.0) released, supporting assigning different LLMs to different Roles. We also introduced [Data Interpreter](https://github.com/geekan/MetaGPT/blob/main/examples/di/README.md), a powerful agent capable of solving a wide range of real-world problems.

🚀 Jan. 16, 2024: Our paper [MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework
](https://arxiv.org/abs/2308.00352) accepted for oral presentation **(top 1.2%)** at ICLR 2024, **ranking #1** in the LLM-based Agent category.

🚀 Jan. 03, 2024: [v0.6.0](https://github.com/geekan/MetaGPT/releases/tag/v0.6.0) released, new features include serialization, upgraded OpenAI package and supported multiple LLM, provided [minimal example for debate](https://github.com/geekan/MetaGPT/blob/main/examples/debate_simple.py) etc.

🚀 Dec. 15, 2023: [v0.5.0](https://github.com/geekan/MetaGPT/releases/tag/v0.5.0) released, introducing some experimental features such as **incremental development**, **multilingual**, **multiple programming languages**, etc.

🔥 Nov. 08, 2023: MetaGPT is selected into [Open100: Top 100 Open Source achievements](https://www.benchcouncil.org/evaluation/opencs/annual.html).

🔥 Sep. 01, 2023: MetaGPT tops GitHub Trending Monthly for the **17th time** in August 2023.

🌟 Jun. 30, 2023: MetaGPT is now open source.

🌟 Apr. 24, 2023: First line of MetaGPT code committed.

## Software Company as Multi-Agent System

1. MetaGPT takes a **one line requirement** as input and outputs **user stories / competitive analysis / requirements / data structures / APIs / documents, etc.**
2. Internally, MetaGPT includes **product managers / architects / project managers / engineers.** It provides the entire process of a **software company along with carefully orchestrated SOPs.**
   1. `Code = SOP(Team)` is the core philosophy. We materialize SOP and apply it to teams composed of LLMs.

![A software company consists of LLM-based roles](docs/resources/software_company_cd.jpeg)

<p align="center">Software Company Multi-Agent Schematic (Gradually Implementing)</p>

## Get Started

### Installation

> Ensure that Python 3.9+ is installed on your system. You can check this by using: `python --version`.  
> You can use conda like this: `conda create -n metagpt python=3.9 && conda activate metagpt`

```bash
pip install --upgrade metagpt
# or `pip install --upgrade git+https://github.com/geekan/MetaGPT.git`
# or `git clone https://github.com/geekan/MetaGPT && cd MetaGPT && pip install --upgrade -e .`
```

For detailed installation guidance, please refer to [cli_install](https://docs.deepwisdom.ai/main/en/guide/get_started/installation.html#install-stable-version)
 or [docker_install](https://docs.deepwisdom.ai/main/en/guide/get_started/installation.html#install-with-docker)

### Configuration

You can init the config of MetaGPT by running the following command, or manually create `~/.metagpt/config2.yaml` file:
```bash
# Check https://docs.deepwisdom.ai/main/en/guide/get_started/configuration.html for more details
metagpt --init-config  # it will create ~/.metagpt/config2.yaml, just modify it to your needs
```

You can configure `~/.metagpt/config2.yaml` according to the [example](https://github.com/geekan/MetaGPT/blob/main/config/config2.example.yaml) and [doc](https://docs.deepwisdom.ai/main/en/guide/get_started/configuration.html):

```yaml
llm:
  api_type: "openai"  # or azure / ollama / open_llm etc. Check LLMType for more options
  model: "gpt-4-turbo"  # or gpt-3.5-turbo-1106 / gpt-4-1106-preview
  base_url: "https://api.openai.com/v1"  # or forward url / other llm url
  api_key: "YOUR_API_KEY"
```

### Usage

After installation, you can use MetaGPT at CLI

```bash
metagpt "Create a 2048 game"  # this will create a repo in ./workspace
```

or use it as library

```python
from metagpt.software_company import generate_repo, ProjectRepo
repo: ProjectRepo = generate_repo("Create a 2048 game")  # or ProjectRepo("<path>")
print(repo)  # it will print the repo structure with files
```

You can also use its [Data Interpreter](https://github.com/geekan/MetaGPT/tree/main/examples/di)

```python
import asyncio
from metagpt.roles.di.data_interpreter import DataInterpreter

async def main():
    di = DataInterpreter()
    await di.run("Run data analysis on sklearn Iris dataset, include a plot")

asyncio.run(main())  # or await main() in a jupyter notebook setting
```


### QuickStart & Demo Video
- Try it on [MetaGPT Huggingface Space](https://huggingface.co/spaces/deepwisdom/MetaGPT)
- [Matthew Berman: How To Install MetaGPT - Build A Startup With One Prompt!!](https://youtu.be/uT75J_KG_aY)
- [Official Demo Video](https://github.com/geekan/MetaGPT/assets/2707039/5e8c1062-8c35-440f-bb20-2b0320f8d27d)

https://github.com/geekan/MetaGPT/assets/34952977/34345016-5d13-489d-b9f9-b82ace413419

## Tutorial

- 🗒 [Online Document](https://docs.deepwisdom.ai/main/en/)
- 💻 [Usage](https://docs.deepwisdom.ai/main/en/guide/get_started/quickstart.html)  
- 🔎 [What can MetaGPT do?](https://docs.deepwisdom.ai/main/en/guide/get_started/introduction.html)
- 🛠 How to build your own agents? 
  - [MetaGPT Usage & Development Guide | Agent 101](https://docs.deepwisdom.ai/main/en/guide/tutorials/agent_101.html)
  - [MetaGPT Usage & Development Guide | MultiAgent 101](https://docs.deepwisdom.ai/main/en/guide/tutorials/multi_agent_101.html)
- 🧑‍💻 Contribution
  - [Develop Roadmap](docs/ROADMAP.md)
- 🔖 Use Cases
  - [Data Interpreter](https://docs.deepwisdom.ai/main/en/guide/use_cases/agent/interpreter/intro.html)
  - [Debate](https://docs.deepwisdom.ai/main/en/guide/use_cases/multi_agent/debate.html)
  - [Researcher](https://docs.deepwisdom.ai/main/en/guide/use_cases/agent/researcher.html)
  - [Recepit Assistant](https://docs.deepwisdom.ai/main/en/guide/use_cases/agent/receipt_assistant.html)
- ❓ [FAQs](https://docs.deepwisdom.ai/main/en/guide/faq.html)

## Support

### Discord Join US

📢 Join Our [Discord Channel](https://discord.gg/ZRHeExS6xv)! Looking forward to seeing you there! 🎉

### Contributor form

📝 [Fill out the form](https://airtable.com/appInfdG0eJ9J4NNL/pagK3Fh1sGclBvVkV/form) to become a contributor. We are looking forward to your participation!

### Contact Information

If you have any questions or feedback about this project, please feel free to contact us. We highly appreciate your suggestions!

- **Email:** alexanderwu@deepwisdom.ai
- **GitHub Issues:** For more technical inquiries, you can also create a new issue in our [GitHub repository](https://github.com/geekan/metagpt/issues).

We will respond to all questions within 2-3 business days.

## Citation

To stay updated with the latest research and development, follow [@MetaGPT_](https://twitter.com/MetaGPT_) on Twitter. 

To cite [MetaGPT](https://arxiv.org/abs/2308.00352) or [Data Interpreter](https://arxiv.org/abs/2402.18679) in publications, please use the following BibTeX entries.

```bibtex
@misc{hong2023metagpt,
      title={MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework}, 
      author={Sirui Hong and Mingchen Zhuge and Jonathan Chen and Xiawu Zheng and Yuheng Cheng and Ceyao Zhang and Jinlin Wang and Zili Wang and Steven Ka Shing Yau and Zijuan Lin and Liyang Zhou and Chenyu Ran and Lingfeng Xiao and Chenglin Wu and Jürgen Schmidhuber},
      year={2023},
      eprint={2308.00352},
      archivePrefix={arXiv},
      primaryClass={cs.AI}
}
@misc{hong2024data,
      title={Data Interpreter: An LLM Agent For Data Science}, 
      author={Sirui Hong and Yizhang Lin and Bang Liu and Bangbang Liu and Binhao Wu and Danyang Li and Jiaqi Chen and Jiayi Zhang and Jinlin Wang and Li Zhang and Lingyao Zhang and Min Yang and Mingchen Zhuge and Taicheng Guo and Tuo Zhou and Wei Tao and Wenyi Wang and Xiangru Tang and Xiangtao Lu and Xiawu Zheng and Xinbing Liang and Yaying Fei and Yuheng Cheng and Zongze Xu and Chenglin Wu},
      year={2024},
      eprint={2402.18679},
      archivePrefix={arXiv},
      primaryClass={cs.AI}
}

```

