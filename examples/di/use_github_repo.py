import asyncio

from metagpt.roles.di.data_interpreter import DataInterpreter

USE_GOT_REPO_REQ = """
This is a link to the GOT github repo: https://github.com/spcl/graph-of-thoughts.git.
Clone it, read the README to understand the usage, install it, and finally run the quick start example.
**Note the config for LLM is at `config/config_got.json`, it's outside the repo path, before using it, you need to copy it into graph-of-thoughts.
** Don't write all codes in one response, each time, just write code for one step.
"""


async def main():
    di = DataInterpreter(tools=["Terminal"])
    await di.run(USE_GOT_REPO_REQ)


if __name__ == "__main__":
    asyncio.run(main())
