"""Base scorer."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict

from metagpt.exp_pool.schema import Score


class BaseScorer(BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abstractmethod
    async def evaluate(self, req: str, resp: str) -> Score:
        """Evaluates the quality of a response relative to a given request."""
