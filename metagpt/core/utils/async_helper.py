import asyncio
import threading
from typing import Any


def run_coroutine_in_new_loop(coroutine) -> Any:
    """Runs a coroutine in a new, separate event loop on a different thread.

    This function is useful when try to execute an async function within a sync function, but encounter the error `RuntimeError: This event loop is already running`.
    """
    new_loop = asyncio.new_event_loop()
    t = threading.Thread(target=lambda: new_loop.run_forever())
    t.start()

    future = asyncio.run_coroutine_threadsafe(coroutine, new_loop)

    try:
        return future.result()
    finally:
        new_loop.call_soon_threadsafe(new_loop.stop)
        t.join()
        new_loop.close()


class NestAsyncio:
    """Make asyncio event loop reentrant."""

    is_applied = False

    @classmethod
    def apply_once(cls):
        """Ensures `nest_asyncio.apply()` is called only once."""
        if not cls.is_applied:
            import nest_asyncio

            nest_asyncio.apply()
            cls.is_applied = True
