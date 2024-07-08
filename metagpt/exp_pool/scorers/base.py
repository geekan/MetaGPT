"""Base scorer."""

from abc import ABC, abstractmethod
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict

from metagpt.exp_pool.schema import Score


class BaseScorer(BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abstractmethod
    async def evaluate(self, func: Callable, result: Any, args: tuple = None, kwargs: dict = None) -> Score:
        """Evaluate the quality of the result produced by the function and parameters.

        Args:
            func (Callable): The function whose result is to be evaluated.
            result (Any): The result produced by the function.
            args (Tuple[Any, ...]): The tuple of arguments that were passed to the function.
            kwargs (Dict[str, Any]): The dictionary of keyword arguments that were passed to the function.

        Example:
            result = await sample(5, name="foo")
            score = await scorer.evaluate(sample, result, args=(5), kwargs={"name": "foo"})
        """
