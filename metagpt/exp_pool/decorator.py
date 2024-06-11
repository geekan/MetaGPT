"""Experience Decorator."""

import asyncio
import functools
import inspect
import json
from typing import Any, Callable, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, model_validator

from metagpt.exp_pool.manager import ExperienceManager, exp_manager
from metagpt.exp_pool.schema import Experience, Metric, QueryType, Score
from metagpt.exp_pool.scorers import ExperienceScorer, SimpleScorer
from metagpt.utils.async_helper import NestAsyncio
from metagpt.utils.exceptions import handle_exception
from metagpt.utils.reflection import get_class_name

ReturnType = TypeVar("ReturnType")


def exp_cache(
    _func: Optional[Callable[..., ReturnType]] = None,
    query_type: QueryType = QueryType.SEMANTIC,
    scorer: Optional[ExperienceScorer] = None,
    manager: Optional[ExperienceManager] = None,
    pass_exps_to_func: bool = False,
):
    """Decorator to get a perfect experience, otherwise, it executes the function, and create a new experience.

    This can be applied to both synchronous and asynchronous functions.

    Args:
        _func: Just to make the decorator more flexible, for example, it can be used directly with @exp_cache by default, without the need for @exp_cache().
        query_type: The type of query to be used when fetching experiences.
        scorer: Evaluate experience. Default SimpleScorer.
        manager: How to fetch, evaluate and save experience, etc. Default exp_manager.
        pass_exps_to_func: To control whether imperfect experiences are passed to the function, if True, the func must have a parameter named 'exps'.
    """

    def decorator(func: Callable[..., ReturnType]) -> Callable[..., ReturnType]:
        @functools.wraps(func)
        async def get_or_create(args: Any, kwargs: Any) -> ReturnType:
            handler = ExpCacheHandler(
                func=func,
                args=args,
                kwargs=kwargs,
                exp_manager=manager,
                exp_scorer=scorer,
                pass_exps_to_func=pass_exps_to_func,
            )

            await handler.fetch_experiences(query_type)
            if exp := handler.get_one_perfect_experience():
                return exp

            await handler.execute_function()
            await handler.process_experience()

            return handler._result

        return ExpCacheHandler.choose_wrapper(func, get_or_create)

    return decorator(_func) if _func else decorator


class ExpCacheHandler(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    func: Callable
    args: Any
    kwargs: Any
    exp_manager: Optional[ExperienceManager] = None
    exp_scorer: Optional[ExperienceScorer] = None
    pass_exps_to_func: bool = False

    _exps: list[Experience] = None
    _result: Any = None
    _score: Score = None
    _req: str = None

    @model_validator(mode="after")
    def initialize(self):
        if self.exp_manager is None:
            self.exp_manager = exp_manager

        if self.exp_scorer is None:
            self.exp_scorer = SimpleScorer()

        self._req = self.generate_req_identifier(self.func, *self.args, **self.kwargs)

        return self

    async def fetch_experiences(self, query_type: QueryType):
        """Fetch a potentially perfect existing experience."""

        self._exps = await self.exp_manager.query_exps(self._req, query_type=query_type)

    def get_one_perfect_experience(self) -> Optional[Experience]:
        return self.exp_manager.extract_one_perfect_exp(self._exps)

    async def execute_function(self):
        """Execute the function, and save the result."""
        self._result = await self._execute_function()

    @handle_exception
    async def process_experience(self):
        """Process experience.

        Evaluates and saves experience.
        Use `handle_exception` to ensure robustness, do not stop subsequent operations.
        """
        await self.evaluate_experience()
        self.save_experience()

    async def evaluate_experience(self):
        """Evaluate the experience, and save the score."""

        self._score = await self.exp_scorer.evaluate(self.func, self._result, self.args, self.kwargs)

    def save_experience(self):
        """Save the new experience."""

        exp = Experience(req=self._req, resp=self._result, metric=Metric(score=self._score))

        self.exp_manager.create_exp(exp)

    @classmethod
    def generate_req_identifier(cls, func, *args, **kwargs) -> str:
        """Generate a unique request identifier for any given function and its arguments.

        Serializing args and kwargs into JSON strings and replacing ',' with '~' and ':' with '!'.

        Return Example:
            SimpleClass.test_method@[1~2]@{"c"!3}
        """
        cls_name = get_class_name(func)
        func_name = f"{cls_name}.{func.__name__}" if cls_name else func.__name__

        if cls_name and args and inspect.isfunction(func):
            args = args[1:]

        args = cls._serialize_and_replace(args)
        kwargs = cls._serialize_and_replace(kwargs)

        return f"{func_name}@{args}@{kwargs}"

    @staticmethod
    def choose_wrapper(func, wrapped_func):
        """Choose how to run wrapped_func based on whether the function is asynchronous."""

        async def async_wrapper(*args, **kwargs):
            return await wrapped_func(args, kwargs)

        def sync_wrapper(*args, **kwargs):
            NestAsyncio.apply_once()
            return asyncio.get_event_loop().run_until_complete(wrapped_func(args, kwargs))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    @classmethod
    def _serialize_and_replace(cls, data):
        json_str = json.dumps(data)
        return json_str.replace(", ", "~").replace(": ", "!")

    async def _execute_function(self):
        if self.pass_exps_to_func:
            return await self._execute_function_with_exps()

        return await self._execute_function_without_exps()

    async def _execute_function_without_exps(self):
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(*self.args, **self.kwargs)

        return self.func(*self.args, **self.kwargs)

    async def _execute_function_with_exps(self):
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(*self.args, **self.kwargs, exps=self._exps)

        return self.func(*self.args, **self.kwargs, exps=self._exps)
