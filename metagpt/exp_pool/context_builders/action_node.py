"""Action Node context builder."""

from typing import Any

from metagpt.exp_pool.context_builders.base import BaseContextBuilder

ACTION_NODE_CONTEXT_TEMPLATE = """
{req}

### Experiences
-----
{exps}
-----

## Instruction
Consider **Experiences** to generate a better answer.
"""


class ActionNodeContextBuilder(BaseContextBuilder):
    async def build(self, req: Any) -> str:
        """Builds the action node context string.

        If there are no experiences, returns the original `req`;
        otherwise returns context with `req` and formatted experiences.
        """

        exps = self.format_exps()

        return ACTION_NODE_CONTEXT_TEMPLATE.format(req=req, exps=exps) if exps else req
