import asyncio

from metagpt.roles.ci.code_interpreter import CodeInterpreter


async def main(requirement: str = ""):
    code_interpreter = CodeInterpreter(use_tools=False, goal=requirement)
    await code_interpreter.run(requirement)


if __name__ == "__main__":
    problem = "At a school, all 60 students play on at least one of three teams: Basketball, Soccer, and Mathletics. 8 students play all three sports, half the students play basketball, and the ratio of the size of the math team to the size of the basketball team to the size of the soccer team is $4:3:2$. How many students at the school play on exactly two teams?"
    requirement = (
        f"This is a math problem:{problem}. You can analyze and solve it step by step or use Python code to solve it."
    )

    asyncio.run(main(requirement))
