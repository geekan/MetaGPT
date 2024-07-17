"""RoleZero context builder."""

import copy
import re
from typing import Any

from metagpt.exp_pool.context_builders.base import BaseContextBuilder


class RoleZeroContextBuilder(BaseContextBuilder):
    async def build(self, req: Any) -> list[dict]:
        """Builds the role zero context string.

        Note:
            1. The expected format for `req`, e.g., [{...}, {"role": "user", "content": "context"}].
            2. Returns the original `req` if it is empty.
            3. Creates a copy of req and replaces the example content in the copied req with actual experiences.
        """

        if not req:
            return req

        exps = self.format_exps()
        if not exps:
            return req

        req_copy = copy.deepcopy(req)

        req_copy[-1]["content"] = self.replace_example_content(req_copy[-1].get("content", ""), exps)

        return req_copy

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
