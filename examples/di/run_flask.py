import asyncio

from metagpt.roles.di.data_interpreter import DataInterpreter

USE_GOT_REPO_REQ = """
Write a service using Flask, create a conda environment and run it, and call the service's interface for validation.
Notice: Don't write all codes in one response, each time, just write code for one step.
"""
# If you have created a conda environment, you can say:
# I have created the conda environment '{env_name}', please use this environment to execute.


async def main():
    di = DataInterpreter(tools=["Terminal", "Editor"])
    await di.run(USE_GOT_REPO_REQ)


if __name__ == "__main__":
    asyncio.run(main())
