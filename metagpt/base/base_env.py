#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : base environment

import typing
from abc import abstractmethod
from typing import Any, Optional

from metagpt.base.base_env_space import BaseEnvAction, BaseEnvObsParams
from metagpt.base.base_serialization import BaseSerialization

if typing.TYPE_CHECKING:
    from metagpt.schema import Message


class BaseEnvironment(BaseSerialization):
    """Base environment"""

    @abstractmethod
    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Implement this to get init observation"""

    @abstractmethod
    def observe(self, obs_params: Optional[BaseEnvObsParams] = None) -> Any:
        """Implement this if you want to get partial observation from the env"""

    @abstractmethod
    def step(self, action: BaseEnvAction) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        """Implement this to feed a action and then get new observation from the env"""

    @abstractmethod
    def publish_message(self, message: "Message", peekable: bool = True) -> bool:
        """Distribute the message to the recipients."""

    @abstractmethod
    async def run(self, k=1):
        """Process all task at once"""
