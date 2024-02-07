import asyncio

from metagpt.roles.ci.code_interpreter import CodeInterpreter


async def main(requirement: str = ""):
    code_interpreter = CodeInterpreter(use_tools=False)
    await code_interpreter.run(requirement)


if __name__ == "__main__":
    requirement = "Run data analysis on sklearn Iris dataset, include a plot"

    asyncio.run(main(requirement))
