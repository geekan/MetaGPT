"""Init experience pool.

Put some useful experiences into the experience pool.
"""

import asyncio

from examples.exp_pool.init_exp_pool.engineer_exps import ENGINEER_EXPERIENCES
from examples.exp_pool.init_exp_pool.team_leader_exps import TEAM_LEADER_EXPERIENCES
from metagpt.exp_pool import exp_manager
from metagpt.exp_pool.schema import EntryType, Experience, Metric, Score
from metagpt.logs import logger


async def add_exp(req: str, resp: str, tag: str, metric: Metric = None):
    exp = Experience(
        req=req,
        resp=resp,
        entry_type=EntryType.MANUAL,
        tag=tag,
        metric=metric or Metric(score=Score(val=10, reason="Manual")),
    )

    exp_manager.config.exp_pool.enable_write = True
    exp_manager.create_exp(exp)
    logger.info(f"New experience created for the request `{req[:10]}`.")


async def add_teamleader_exps():
    tag = "TeamLeader.llm_cached_aask"

    for req, resp in TEAM_LEADER_EXPERIENCES:
        await add_exp(req=req, resp=resp, tag=tag)


async def add_engineer_exps():
    tag = "Engineer2.llm_cached_aask"

    for req, resp in ENGINEER_EXPERIENCES:
        await add_exp(req=req, resp=resp, tag=tag)


def query_exps_count():
    count = exp_manager.get_exps_count()
    logger.info(f"Experiences Count: {count}")


async def main():
    await add_teamleader_exps()
    await add_engineer_exps()
    query_exps_count()


if __name__ == "__main__":
    asyncio.run(main())
