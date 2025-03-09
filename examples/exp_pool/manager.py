"""
Demonstrate the creation and querying of experiences.

This script creates a new experience, logs its creation, and then queries for experiences matching the same request.
"""

import asyncio

from metagpt.exp_pool import get_exp_manager
from metagpt.exp_pool.schema import EntryType, Experience
from metagpt.logs import logger


async def main():
    # Define the simple request and response
    req = "Simple req"
    resp = "Simple resp"

    # Add the new experience
    exp = Experience(req=req, resp=resp, entry_type=EntryType.MANUAL)
    exp_manager = get_exp_manager()
    exp_manager.create_exp(exp)
    logger.info(f"New experience created for the request `{req}`.")

    # Query for experiences matching the request
    exps = await exp_manager.query_exps(req)
    logger.info(f"Got experiences: {exps}")


if __name__ == "__main__":
    asyncio.run(main())
