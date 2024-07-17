"""Simple Serializer."""

from typing import Any

from metagpt.exp_pool.serializers.base import BaseSerializer


class SimpleSerializer(BaseSerializer):
    def serialize_req(self, **kwargs) -> str:
        """Just use `str` to convert the request object into a string."""

        return str(kwargs.get("req", ""))

    def serialize_resp(self, resp: Any) -> str:
        """Just use `str` to convert the response object into a string."""

        return str(resp)

    def deserialize_resp(self, resp: str) -> Any:
        """Just return the string response as it is."""

        return resp
