import asyncio
from typing import AsyncGenerator, Awaitable, Callable

from pydantic import BaseModel, ConfigDict, Field

from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message


class SubscriptionRunner(BaseModel):
    """A simple wrapper to manage subscription tasks for different roles using asyncio.

    Example:
        >>> import asyncio
        >>> from metagpt.address import SubscriptionRunner
        >>> from metagpt.roles import Searcher
        >>> from metagpt.schema import Message

        >>> async def trigger():
        ...     while True:
        ...         yield Message(content="the latest news about OpenAI")
        ...         await asyncio.sleep(3600 * 24)

        >>> async def callback(msg: Message):
        ...     print(msg.content)

        >>> async def main():
        ...     pb = SubscriptionRunner()
        ...     await pb.subscribe(Searcher(), trigger(), callback)
        ...     await pb.run()

        >>> asyncio.run(main())
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    tasks: dict[Role, asyncio.Task] = Field(default_factory=dict)

    async def subscribe(
        self,
        role: Role,
        trigger: AsyncGenerator[Message, None],
        callback: Callable[
            [
                Message,
            ],
            Awaitable[None],
        ],
    ):
        """Subscribes a role to a trigger and sets up a callback to be called with the role's response.

        Args:
            role: The role to subscribe.
            trigger: An asynchronous generator that yields Messages to be processed by the role.
            callback: An asynchronous function to be called with the response from the role.
        """
        loop = asyncio.get_running_loop()

        async def _start_role():
            async for msg in trigger:
                resp = await role.run(msg)
                await callback(resp)

        self.tasks[role] = loop.create_task(_start_role(), name=f"Subscription-{role}")

    async def unsubscribe(self, role: Role):
        """Unsubscribes a role from its trigger and cancels the associated task.

        Args:
            role: The role to unsubscribe.
        """
        task = self.tasks.pop(role)
        task.cancel()

    async def run(self, raise_exception: bool = True):
        """Runs all subscribed tasks and handles their completion or exception.

        Args:
            raise_exception: _description_. Defaults to True.

        Raises:
            task.exception: _description_
        """
        while True:
            for role, task in self.tasks.items():
                if task.done():
                    if task.exception():
                        if raise_exception:
                            raise task.exception()
                        logger.opt(exception=task.exception()).error(f"Task {task.get_name()} run error")
                    else:
                        logger.warning(
                            f"Task {task.get_name()} has completed. "
                            "If this is unexpected behavior, please check the trigger function."
                        )
                    self.tasks.pop(role)
                    break
            else:
                await asyncio.sleep(1)
