"""Experience Decorator."""

import asyncio
import functools
from typing import Any, Callable, Optional, TypeVar

from metagpt.exp_pool.manager import exp_manager
from metagpt.exp_pool.schema import Experience
from metagpt.utils.async_helper import NestAsyncio

ReturnType = TypeVar("ReturnType")


def exp_cache(_func: Optional[Callable[..., ReturnType]] = None):
    """Decorator to check for a perfect experience and returns it if exists.

    Otherwise, it executes the function, save the result as a new experience, and returns the result.

    This can be applied to both synchronous and asynchronous functions.
    """

    def decorator(func: Callable[..., ReturnType]) -> Callable[..., ReturnType]:
        @functools.wraps(func)
        async def get_or_create(args: Any, kwargs: Any, is_async: bool) -> ReturnType:
            """Attempts to retrieve a perfect experience or creates an experience if not found."""

            # 1. Get exps.
            req = f"{func.__name__}_{args}_{kwargs}"
            exps = await exp_manager.query_exps(req)
            if perfect_exp := exp_manager.extract_one_perfect_exp(exps):
                return perfect_exp

            # 2. Exec func. TODO: pass exps to func
            if is_async:
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 3. Create an exp.
            exp_manager.create_exp(Experience(req=req, resp=result))

            return result

        def sync_wrapper(*args: Any, **kwargs: Any) -> ReturnType:
            NestAsyncio.apply_once()
            return asyncio.get_event_loop().run_until_complete(get_or_create(args, kwargs, is_async=False))

        async def async_wrapper(*args: Any, **kwargs: Any) -> ReturnType:
            return await get_or_create(args, kwargs, is_async=True)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    if _func is None:
        return decorator
    else:
        return decorator(_func)
