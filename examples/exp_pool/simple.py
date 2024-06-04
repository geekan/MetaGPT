"""Simple example of experience pool."""

import asyncio

from metagpt.exp_pool import exp_manager
from metagpt.exp_pool.schema import EntryType, Experience
from metagpt.logs import logger


async def main():
    req = "Simple task."
    resp = "Simple echo."
    exp = Experience(req=req, resp=resp, entry_type=EntryType.MANUAL)

    exp_manager.create_exp(exp)
    logger.info(f"New experience created for the request `{req}`.")

    exps = await exp_manager.query_exps(req)
    logger.info(f"Got experiences: {exps}")


if __name__ == "__main__":
    asyncio.run(main())
