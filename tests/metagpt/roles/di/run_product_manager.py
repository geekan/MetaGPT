import asyncio

from metagpt.roles.product_manager import ProductManager

WRITE_2048 = """Write a PRD for a cli 2048 game"""

REWRITE_2048 = """Rewrite the prd at /Users/gary/Files/temp/workspace/2048_game/docs/prd.json, add a web UI"""

CASUAL_CHAT = """What's your name?"""


async def main(requirement):
    product_manager = ProductManager()
    await product_manager.run(requirement)


if __name__ == "__main__":
    asyncio.run(main(WRITE_2048))
