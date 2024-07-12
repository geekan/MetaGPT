"""Simple context builder."""


from typing import Any

from metagpt.exp_pool.context_builders.base import BaseContextBuilder

SIMPLE_CONTEXT_TEMPLATE = """
## Context

### Experiences
-----
{exps}
-----

## User Requirement
{req}

## Instruction
Consider **Experiences** to generate a better answer.
"""


class SimpleContextBuilder(BaseContextBuilder):
    async def build(self, req: Any) -> str:
        return SIMPLE_CONTEXT_TEMPLATE.format(req=req, exps=self.format_exps())
