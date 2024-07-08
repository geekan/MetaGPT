"""Base context builder."""

import re
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict

from metagpt.exp_pool.schema import Experience

EXP_TEMPLATE = """Given the request: {req}, We can get the response: {resp}, Which scored: {score}."""


class BaseContextBuilder(BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    exps: list[Experience] = []

    @abstractmethod
    async def build(self, *args, **kwargs) -> Any:
        """Build context from parameters."""

    def format_exps(self) -> str:
        """Format experiences into a numbered list of strings."""

        result = []
        for i, exp in enumerate(self.exps, start=1):
            score_val = exp.metric.score.val if exp.metric and exp.metric.score else "N/A"
            result.append(f"{i}. " + EXP_TEMPLATE.format(req=exp.req, resp=exp.resp, score=score_val))

        return "\n".join(result)

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
