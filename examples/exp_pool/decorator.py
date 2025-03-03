"""
This script demonstrates how to automatically store experiences using @exp_cache and query the stored experiences.
"""

import asyncio
import uuid

from metagpt.exp_pool import exp_cache, get_exp_manager
from metagpt.logs import logger


@exp_cache()
async def produce(req=""):
    return f"{req} {uuid.uuid4().hex}"


async def main():
    req = "Water"

    resp = await produce(req=req)
    logger.info(f"The response of `produce({req})` is: {resp}")

    exps = await get_exp_manager().query_exps(req)
    logger.info(f"Find experiences: {exps}")


if __name__ == "__main__":
    asyncio.run(main())
