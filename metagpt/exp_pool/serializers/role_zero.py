"""RoleZero Serializer."""

import copy
import json

from metagpt.exp_pool.serializers.simple import SimpleSerializer


class RoleZeroSerializer(SimpleSerializer):
    def serialize_req(self, **kwargs) -> str:
        """Serialize the request for database storage, ensuring it is a string.

        Only extracts the necessary content from `req` because `req` may be very lengthy and could cause embedding errors.

        Args:
            req (list[dict]): The request to be serialized. Example:
                [
                    {"role": "user", "content": "..."},
                    {"role": "assistant", "content": "..."},
                    {"role": "user", "content": "context"},
                ]

        Returns:
            str: The serialized request as a JSON string.
        """
        req = kwargs.get("req", [])

        if not req:
            return ""

        filtered_req = self._filter_req(req)

        if state_data := kwargs.get("state_data"):
            filtered_req.append({"role": "user", "content": state_data})

        return json.dumps(filtered_req)

    def _filter_req(self, req: list[dict]) -> list[dict]:
        """Filter the `req` to include only necessary items.

        Args:
            req (list[dict]): The original request.

        Returns:
            list[dict]: The filtered request.
        """

        filtered_req = [copy.deepcopy(item) for item in req if self._is_useful_content(item["content"])]

        return filtered_req

    def _is_useful_content(self, content: str) -> bool:
        """Currently, only the content of the file is considered, and more judgments can be added later."""

        if "Command Editor.read executed: file_path" in content:
            return True

        return False
