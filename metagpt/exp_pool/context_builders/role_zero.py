"""RoleZero context builder."""
import copy
import json

from metagpt.exp_pool.context_builders.base import BaseContextBuilder


class RoleZeroContextBuilder(BaseContextBuilder):
    async def build(self, *args, **kwargs) -> list[dict]:
        """Builds the context by updating the req with formatted experiences.

        If there are no experiences, retains the original examples in req, otherwise replaces the examples with the formatted experiences.
        """

        req = kwargs.get("req", [])
        if not req:
            return req

        exps_str = self.format_exps()
        if not exps_str:
            return req

        req[-1]["content"] = self.replace_example_content(req[-1].get("content", ""), exps_str)

        return req

    def replace_example_content(self, text: str, new_example_content: str) -> str:
        return self.replace_content_between_markers(text, "# Example", "# Instruction", new_example_content)

    @staticmethod
    def req_serialize(req: list[dict]) -> str:
        """Serialize the request for database storage, ensuring it is a string.

        This function deep copies the request and modifies the content of the last element
        to remove unnecessary sections, making the request more concise.
        """

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
