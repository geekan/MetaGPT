import asyncio

from metagpt.roles.ci.code_interpreter import CodeInterpreter


async def main(requirement: str):
    role = CodeInterpreter(auto_run=True, use_tools=False)
    await role.run(requirement)


if __name__ == "__main__":
    requirement = "Run data analysis on sklearn Wine recognition dataset, include a plot, and train a model to predict wine class (20% as validation), and show validation accuracy."
    asyncio.run(main(requirement))
