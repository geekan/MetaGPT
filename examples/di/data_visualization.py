import asyncio

from metagpt.logs import logger
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.utils.recovery_util import save_history


async def main(requirement: str = ""):
    di = DataInterpreter()
    rsp = await di.run(requirement)
    logger.info(rsp)
    save_history(role=di)


if __name__ == "__main__":
    requirement = "在sklearn Iris数据集上运行数据分析，包括一个图"
    asyncio.run(main(requirement))
