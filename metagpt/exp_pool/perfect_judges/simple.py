"""Simple perfect judge."""


from pydantic import ConfigDict

from metagpt.exp_pool.perfect_judges.base import BasePerfectJudge
from metagpt.exp_pool.schema import MAX_SCORE, Experience


class SimplePerfectJudge(BasePerfectJudge):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def is_perfect_exp(self, exp: Experience, serialized_req: str, *args, **kwargs) -> bool:
        """Determine whether the experience is perfect.

        Args:
            exp (Experience): The experience to evaluate.
            serialized_req (str): The serialized request to compare against the experience's request.

        Returns:
            bool: True if the serialized request matches the experience's request and the experience's score is perfect, False otherwise.
        """

        if not exp.metric or not exp.metric.score:
            return False

        return serialized_req == exp.req and exp.metric.score.val == MAX_SCORE
