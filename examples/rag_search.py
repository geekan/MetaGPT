"""Agent with RAG search."""

import asyncio

from examples.rag_pipeline import DOC_PATH, QUESTION
from metagpt.logs import logger
from metagpt.rag.engines import SimpleEngine
from metagpt.roles import Sales


async def search():
    """Agent with RAG search."""

    store = SimpleEngine.from_docs(input_files=[DOC_PATH])
    role = Sales(profile="Sales", store=store)
    result = await role.run(QUESTION)
    logger.info(result)


if __name__ == "__main__":
    asyncio.run(search())
