"""RoleZero context builder."""

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
