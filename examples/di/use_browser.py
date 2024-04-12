import asyncio

from metagpt.roles.di.data_interpreter import DataInterpreter

# an example to showcase navigation
MG_LLM_CONFIG_REQ = """
This is a link to the doc site of MetaGPT project: https://docs.deepwisdom.ai/main/en/
Check where you can go to on the site and try to find out the list of LLM APIs supported by MetaGPT.
Don't write all codes in one response, each time, just write code for one step.
"""

# an example to showcase searching
PAPER_LIST_REQ = """"
At https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,
find the first paper whose title includes `multiagent`, open it and summarize its abstract.
Don't write all codes in one response, each time, just write code for one step.
"""


async def main():
    di = DataInterpreter(tools=["Browser"], react_mode="react")
    await di.run(MG_LLM_CONFIG_REQ)


if __name__ == "__main__":
    asyncio.run(main())
