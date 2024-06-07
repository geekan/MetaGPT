import asyncio

from metagpt.exp_pool.scorers import SimpleScorer
from metagpt.logs import logger


def echo(req: str):
    """Echo from req."""

    return req


async def simple():
    scorer = SimpleScorer()

    score = await scorer.evaluate(echo, "data", ("data",))
    logger.info(f"The score is: {score}")


async def main():
    await simple()


if __name__ == "__main__":
    asyncio.run(main())
