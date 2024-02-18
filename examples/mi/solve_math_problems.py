import asyncio

from metagpt.roles.mi.interpreter import Interpreter


async def main(requirement: str = ""):
    mi = Interpreter(use_tools=False)
    await mi.run(requirement)


if __name__ == "__main__":
    requirement = "Solve this math problem: The greatest common divisor of positive integers m and n is 6. The least common multiple of m and n is 126. What is the least possible value of m + n?"
    asyncio.run(main(requirement))
