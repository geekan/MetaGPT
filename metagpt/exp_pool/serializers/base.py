"""Base serializer."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseSerializer(BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abstractmethod
    def serialize_req(self, **kwargs) -> str:
        """Serializes the request for storage.

        Do not modify kwargs. If modification is necessary, use copy.deepcopy to create a copy first.
        Note that copy.deepcopy may raise errors, such as TypeError: cannot pickle '_thread.RLock' object.
        """

    @abstractmethod
    def serialize_resp(self, resp: Any) -> str:
        """Serializes the function's return value for storage.

        Do not modify resp. The rest is the same as `serialize_req`.
        """

    @abstractmethod
    def deserialize_resp(self, resp: str) -> Any:
        """Deserializes the stored response back to the function's return value"""
