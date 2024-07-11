"""RoleZero context builder."""

import re

from metagpt.exp_pool.context_builders.base import BaseContextBuilder


class RoleZeroContextBuilder(BaseContextBuilder):
    async def build(self, **kwargs) -> list[dict]:
        """Builds the context by updating the req with formatted experiences.

        Args:
            **kwargs: Arbitrary keyword arguments, expecting 'req' as a key.

        Returns:
            list[dict]: The updated request with formatted experiences or the original request if no experiences are available.
        """
        req = kwargs.get("req", [])
        if not req:
            return req

        exps = self.format_exps()
        if not exps:
            return req

        req[-1]["content"] = self.replace_example_content(req[-1].get("content", ""), exps)

        return req

    def replace_example_content(self, text: str, new_example_content: str) -> str:
        return self.replace_content_between_markers(text, "# Example", "# Instruction", new_example_content)

    @staticmethod
    def replace_content_between_markers(text: str, start_marker: str, end_marker: str, new_content: str) -> str:
        """Replace the content between `start_marker` and `end_marker` in the text with `new_content`.

        Args:
            text (str): The original text.
            new_content (str): The new content to replace the old content.
            start_marker (str): The marker indicating the start of the content to be replaced, such as '# Example'.
            end_marker (str): The marker indicating the end of the content to be replaced, such as '# Instruction'.

        Returns:
            str: The text with the content replaced.
        """

        pattern = re.compile(f"({start_marker}\n)(.*?)(\n{end_marker})", re.DOTALL)

        def replacement(match):
            return f"{match.group(1)}{new_content}\n{match.group(3)}"

        replaced_text = pattern.sub(replacement, text)
        return replaced_text
