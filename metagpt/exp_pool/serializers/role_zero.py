"""RoleZero Serializer."""

import copy
import json

from metagpt.exp_pool.context_builders import RoleZeroContextBuilder
from metagpt.exp_pool.serializers.simple import SimpleSerializer


class RoleZeroSerializer(SimpleSerializer):
    def serialize_req(self, req: list[dict]) -> str:
        """Serialize the request for database storage, ensuring it is a string.

        This function modifies the content of the last element in the request to remove unnecessary sections,
        making the request more concise.

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

        req_copy = copy.deepcopy(req)
        last_content = req_copy[-1]["content"]
        last_content = RoleZeroContextBuilder.replace_content_between_markers(
            last_content, "# Data Structure", "# Current Plan", ""
        )
        last_content = RoleZeroContextBuilder.replace_content_between_markers(
            last_content, "# Example", "# Instruction", ""
        )

        req_copy[-1]["content"] = last_content

        return json.dumps(req_copy)
