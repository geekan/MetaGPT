from metagpt.exp_pool.manager import ExperiencePoolManager
from metagpt.exp_pool.schema import Experience
from pprint import pprint
import asyncio
# import logging
# logging.basicConfig(level=logging.DEBUG)

async def main():
    req = "2048 game"
    exp = Experience(req=req, resp="python code")

    manager = ExperiencePoolManager()

    # pprint(manager.storage.get())
    # manager.create_exp(exp)
    result = await manager.query_exp(req)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())