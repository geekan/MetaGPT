import asyncio
from metagpt.config import Config
from metagpt.roles import Searcher
from metagpt.tools import SearchEngineType

async def main():
    await Searcher(engine = SearchEngineType.SERPER_GOOGLE).run("What are the best ski brands for advanced skiers?")


asyncio.run(main())
