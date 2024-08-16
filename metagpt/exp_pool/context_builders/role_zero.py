"""RoleZero context builder."""

import copy
from typing import Any

from metagpt.const import EXPERIENCE_MASK
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
        return self.fill_experience(text, new_example_content)

    @staticmethod
    def fill_experience(text: str, new_example_content: str) -> str:
        replaced_text = text.replace(EXPERIENCE_MASK, new_example_content)
        return replaced_text
