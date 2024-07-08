"""Simple context builder."""


from metagpt.exp_pool.context_builders.base import BaseContextBuilder

SIMPLE_CONTEXT_TEMPLATE = """
{req}

### Experiences
-----
{exps}
-----

## Instruction
Consider **Experiences** to generate a better answer.
"""


class SimpleContextBuilder(BaseContextBuilder):
    async def build(self, *args, **kwargs) -> str:
        req = kwargs.get("req", "")
        exps = self.format_exps()

        return SIMPLE_CONTEXT_TEMPLATE.format(req=req, exps=exps) if exps else req
