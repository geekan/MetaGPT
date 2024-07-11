"""RoleZero Serializer."""

import copy
import json

from metagpt.exp_pool.context_builders import RoleZeroContextBuilder
from metagpt.exp_pool.serializers.simple import SimpleSerializer


class RoleZeroSerializer(SimpleSerializer):
    def serialize_req(self, req: list[dict]) -> str:
        """Serialize the request for database storage, ensuring it is a string.

        This function does not modify `req`; it only extracts the necessary content from `req` because `req` may be very lengthy and could cause embedding errors.

        Args:
            req (list[dict]): The request to be serialized. Example:
                [
                    {"role": "user", "content": "..."},
                    {"role": "assistant", "content": "..."},
                    {"role": "user", "content": "..."},
                ]

        Returns:
            str: The serialized request as a JSON string.
        """
        if not req:
            return ""

        filtered_req = self._filter_req(req)
        self._clean_last_entry_content(filtered_req)

        return json.dumps(filtered_req)

    def _filter_req(self, req: list[dict]) -> list[dict]:
        """Filter the request to include only necessary items and the last entry.

        Args:
            req (list[dict]): The original request.

        Returns:
            list[dict]: The filtered request.
        """

        filtered_req = [
            copy.deepcopy(item) for item in req if "Command Editor.read executed: file_path" in item["content"]
        ]
        filtered_req.append(copy.deepcopy(req[-1]))

        return filtered_req

    def _clean_last_entry_content(self, req: list[dict]):
        """Modifies the content of the last element in the request to remove unnecessary sections, making the request more concise."""

        last_content = req[-1]["content"]

        last_content = RoleZeroContextBuilder.replace_content_between_markers(
            last_content, "# Data Structure", "# Current Plan", ""
        )
        last_content = RoleZeroContextBuilder.replace_content_between_markers(
            last_content, "# Example", "# Instruction", ""
        )

        req[-1]["content"] = last_content
