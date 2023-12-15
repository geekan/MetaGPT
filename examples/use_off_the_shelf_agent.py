"""
Filename: MetaGPT/examples/use_off_the_shelf_agent.py
Created Date: Tuesday, September 19th 2023, 6:52:25 pm
Author: garylin2099
"""
import asyncio

from metagpt.logs import logger
from metagpt.roles.product_manager import ProductManager


async def main():
    msg = "Write a PRD for a snake game"
    role = ProductManager()
    result = await role.run(msg)
    logger.info(result.content[:100])


if __name__ == "__main__":
    asyncio.run(main())
