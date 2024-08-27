"""Init experience pool.

Put some useful experiences into the experience pool.
"""

import asyncio
import json
from pathlib import Path

from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.exp_pool import get_exp_manager
from metagpt.exp_pool.schema import EntryType, Experience, Metric, Score
from metagpt.logs import logger
from metagpt.utils.common import aread


async def load_file(filepath) -> list[dict]:
    """Asynchronously loads and parses a JSON file.

    Args:
        filepath: Path to the JSON file.

    Returns:
        A list of dictionaries parsed from the JSON file.
    """

    return json.loads(await aread(filepath))


async def add_exp(req: str, resp: str, tag: str, metric: Metric = None):
    """Adds a new experience to the experience pool.

    Args:
        req: The request string.
        resp: The response string.
        tag: A tag for categorizing the experience.
        metric: Optional metric for the experience. Defaults to a score of 10.

    """

    exp = Experience(
        req=req,
        resp=resp,
        entry_type=EntryType.MANUAL,
        tag=tag,
        metric=metric or Metric(score=Score(val=10, reason="Manual")),
    )
    exp_manager = get_exp_manager()
    exp_manager.is_writable = True

    exp_manager.create_exp(exp)
    logger.info(f"New experience created for the request `{req[:10]}`.")


async def add_exps(exps: list, tag: str):
    """Adds multiple experiences to the experience pool.

    Args:
        exps: A list of experience dictionaries.
        tag: A tag for categorizing the experiences.

    """
    tasks = [
        add_exp(req=exp["req"] if isinstance(exp["req"], str) else json.dumps(exp["req"]), resp=exp["resp"], tag=tag)
        for exp in exps
    ]
    await asyncio.gather(*tasks)


async def add_exps_from_file(tag: str, filepath: Path):
    """Loads experiences from a file and adds them to the experience pool.

    Args:
        tag: A tag for categorizing the experiences.
        filepath: Path to the file containing experiences.

    """

    exps = await load_file(filepath)
    await add_exps(exps, tag)


def query_exps_count():
    """Queries and logs the total count of experiences in the pool."""
    exp_manager = get_exp_manager()
    count = exp_manager.get_exps_count()
    logger.info(f"Experiences Count: {count}")


async def main():
    await add_exps_from_file("TeamLeader.llm_cached_aask", EXAMPLE_DATA_PATH / "exp_pool/team_leader_exps.json")
    await add_exps_from_file("Engineer2.llm_cached_aask", EXAMPLE_DATA_PATH / "exp_pool/engineer_exps.json")
    query_exps_count()


if __name__ == "__main__":
    asyncio.run(main())
