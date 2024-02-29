import asyncio

from metagpt.roles.mi.interpreter import Interpreter


async def main(requirement: str = ""):
    mi = Interpreter(use_tools=False)
    await mi.run(requirement)


if __name__ == "__main__":
    requirement = "Run data analysis on sklearn Iris dataset, include a plot"

    asyncio.run(main(requirement))
