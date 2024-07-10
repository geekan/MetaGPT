"""Action Node context builder."""


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
    async def build(self, **kwargs) -> str:
        """Builds the action node context string.

        Args:
            **kwargs: Arbitrary keyword arguments, expecting 'req' as a key.

        Returns:
            str: The formatted context string using the request and formatted experiences.
                 If no experiences are available, returns the request as is.
        """
        req = kwargs.get("req", "")
        exps = self.format_exps()

        return ACTION_NODE_CONTEXT_TEMPLATE.format(req=req, exps=exps) if exps else req
