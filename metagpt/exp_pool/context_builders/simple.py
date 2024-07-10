"""Simple context builder."""


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
    async def build(self, **kwargs) -> str:
        return SIMPLE_CONTEXT_TEMPLATE.format(req=kwargs.get("req", ""), exps=self.format_exps())
