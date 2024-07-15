"""Base context builder."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict

from metagpt.exp_pool.schema import Experience

EXP_TEMPLATE = """Given the request: {req}, We can get the response: {resp}, which scored: {score}."""


class BaseContextBuilder(BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    exps: list[Experience] = []

    @abstractmethod
    async def build(self, req: Any) -> Any:
        """Build context from req.

        Do not modify `req`. If modification is necessary, use copy.deepcopy to create a copy first.
        """

    def format_exps(self) -> str:
        """Format experiences into a numbered list of strings.

        Example:
            1. Given the request: req1, We can get the response: resp1, which scored: 8.
            2. Given the request: req2, We can get the response: resp2, which scored: 9.

        Returns:
            str: The formatted experiences as a string.
        """

        result = []
        for i, exp in enumerate(self.exps, start=1):
            score_val = exp.metric.score.val if exp.metric and exp.metric.score else "N/A"
            result.append(f"{i}. " + EXP_TEMPLATE.format(req=exp.req, resp=exp.resp, score=score_val))

        return "\n".join(result)
