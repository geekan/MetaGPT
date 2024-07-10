"""Base serializer."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseSerializer(BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abstractmethod
    def serialize_req(self, req: Any) -> str:
        """Serializes the request for storage."""

    @abstractmethod
    def serialize_resp(self, resp: Any) -> str:
        """Serializes the function's return value for storage."""

    @abstractmethod
    def deserialize_resp(self, resp: str) -> Any:
        """Deserializes the stored response back to the function's return value"""
