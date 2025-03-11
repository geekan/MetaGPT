
# MetaGPT: The Multi-Agent Framework

<p align="center">
<a href=""><img src="docs/resources/MetaGPT-new-log.png" alt="MetaGPT logo: Enable GPT to work in a software company, collaborating to tackle more complex tasks." width="150px"></a>
</p>

<p align="center">
[ <b>En</b> |
<a href="docs/README_CN.md">中</a> |
<a href="docs/README_FR.md">Fr</a> |
<a href="docs/README_JA.md">日</a> ]
<b>Assign different roles to GPTs to form a collaborative entity for complex tasks.</b>
</p>

<p align="center">
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
<a href="https://discord.gg/DYn29wFk9z"><img src="https://dcbadge.vercel.app/api/server/DYn29wFk9z?style=flat" alt="Discord Follow"></a>
<a href="https://twitter.com/MetaGPT_"><img src="https://img.shields.io/twitter/follow/MetaGPT?style=social" alt="Twitter Follow"></a>
</p>

<h4 align="center">
    
</h4>

## News

🚀 Mar. 10, 2025: 🎉 [mgx.dev](https://mgx.dev/) is the #1 Product of the Week on @ProductHunt! 🏆

🚀 Mar. &nbsp; 4, 2025: 🎉 [mgx.dev](https://mgx.dev/) is the #1 Product of the Day on @ProductHunt! 🏆

🚀 Feb. 19, 2025: Today we are officially launching our natural language programming product: [MGX (MetaGPT X)](https://mgx.dev/) - the world's first AI agent development team. More details on [Twitter](https://x.com/MetaGPT_/status/1892199535130329356).

🚀 Feb. 17, 2025: We introduced two papers: [SPO](https://arxiv.org/pdf/2502.06855) and [AOT](https://arxiv.org/pdf/2502.12018), check the [code](examples)!

🚀 Jan. 22, 2025: Our paper [AFlow: Automating Agentic Workflow Generation](https://openreview.net/forum?id=z5uVAKwmjf) accepted for **oral presentation (top 1.8%)** at ICLR 2025, **ranking #2** in the LLM-based Agent category.

👉👉 [Earlier news](docs/NEWS.md) 

## Software Company as Multi-Agent System

1. MetaGPT takes a **one line requirement** as input and outputs **user stories / competitive analysis / requirements / data structures / APIs / documents, etc.**
2. Internally, MetaGPT includes **product managers / architects / project managers / engineers.** It provides the entire process of a **software company along with carefully orchestrated SOPs.**
   1. `Code = SOP(Team)` is the core philosophy. We materialize SOP and apply it to teams composed of LLMs.

![A software company consists of LLM-based roles](docs/resources/software_company_cd.jpeg)

<p align="center">Software Company Multi-Agent Schematic (Gradually Implementing)</p>

## Get Started

### Installation

> Ensure that Python 3.9 or later, but less than 3.12, is installed on your system. You can check this by using: `python --version`.  
> You can use conda like this: `conda create -n metagpt python=3.9 && conda activate metagpt`

```bash
pip install --upgrade metagpt
# or `pip install --upgrade git+https://github.com/geekan/MetaGPT.git`
# or `git clone https://github.com/geekan/MetaGPT && cd MetaGPT && pip install --upgrade -e .`
```

**Install [node](https://nodejs.org/en/download) and [pnpm](https://pnpm.io/installation#using-npm) before actual use.**

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
  api_type: "openai"  # or azure / ollama / groq etc. Check LLMType for more options
  model: "gpt-4-turbo"  # or gpt-3.5-turbo
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
from metagpt.software_company import generate_repo
from metagpt.utils.project_repo import ProjectRepo

repo: ProjectRepo = generate_repo("Create a 2048 game")  # or ProjectRepo("<path>")
print(repo)  # it will print the repo structure with files
```

You can also use [Data Interpreter](https://github.com/geekan/MetaGPT/tree/main/examples/di) to write code:

```python
import asyncio
from metagpt.roles.di.data_interpreter import DataInterpreter

async def main():
    di = DataInterpreter()
    await di.run("Run data analysis on sklearn Iris dataset, include a plot")

asyncio.run(main())  # or await main() in a jupyter notebook setting
```


### QuickStart & Demo Video
- Try it on [MetaGPT Huggingface Space](https://huggingface.co/spaces/deepwisdom/MetaGPT-SoftwareCompany)
- [Matthew Berman: How To Install MetaGPT - Build A Startup With One Prompt!!](https://youtu.be/uT75J_KG_aY)
- [Official Demo Video](https://github.com/geekan/MetaGPT/assets/2707039/5e8c1062-8c35-440f-bb20-2b0320f8d27d)

https://github.com/user-attachments/assets/888cb169-78c3-4a42-9d62-9d90ed3928c9

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
  - [Receipt Assistant](https://docs.deepwisdom.ai/main/en/guide/use_cases/agent/receipt_assistant.html)
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

To cite [MetaGPT](https://openreview.net/forum?id=VtmBAGCN7o) in publications, please use the following BibTeX entries.   

```bibtex
@inproceedings{hong2024metagpt,
      title={Meta{GPT}: Meta Programming for A Multi-Agent Collaborative Framework},
      author={Sirui Hong and Mingchen Zhuge and Jonathan Chen and Xiawu Zheng and Yuheng Cheng and Jinlin Wang and Ceyao Zhang and Zili Wang and Steven Ka Shing Yau and Zijuan Lin and Liyang Zhou and Chenyu Ran and Lingfeng Xiao and Chenglin Wu and J{\"u}rgen Schmidhuber},
      booktitle={The Twelfth International Conference on Learning Representations},
      year={2024},
      url={https://openreview.net/forum?id=VtmBAGCN7o}
}
```

For more work, please refer to [Academic Work](docs/ACADEMIC_WORK.md).
