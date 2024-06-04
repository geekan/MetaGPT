"""Simple example of experience pool."""

import asyncio

from metagpt.exp_pool import exp_manager
from metagpt.exp_pool.schema import EntryType, Experience
from metagpt.logs import logger


async def main():
    req = "Simple task."

    # 1. Find experiences.
    exps = await exp_manager.query_exps(req)
    if exps:
        logger.info(f"Experiences already exist for the request `{req}`: {exps}")
        return

    # 2. Create a new experience if none exist
    exp_manager.create_exp(Experience(req=req, resp="Simple echo.", entry_type=EntryType.MANUAL))
    logger.info(f"New experience created for the request `{req}`.")

    # 3. Find again
    exps = await exp_manager.query_exps(req)
    logger.info(f"Updated experiences: {exps}")


if __name__ == "__main__":
    asyncio.run(main())
