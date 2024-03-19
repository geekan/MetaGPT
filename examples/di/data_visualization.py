import asyncio

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main(requirement: str = ""):
    di = DataInterpreter()
    await di.run(requirement)


if __name__ == "__main__":
    requirement = "Run data analysis on sklearn Iris dataset, include a plot"

    asyncio.run(main(requirement))
