import pytest

from metagpt.exp_pool.context_builders.base import (
    EXP_TEMPLATE,
    BaseContextBuilder,
    Experience,
)
from metagpt.exp_pool.schema import Metric, Score


class TestBaseContextBuilder:
    class ConcreteContextBuilder(BaseContextBuilder):
        async def build(self, *args, **kwargs):
            pass

    @pytest.fixture
    def context_builder(self):
        return self.ConcreteContextBuilder()

    def test_format_exps(self, context_builder):
        exp1 = Experience(req="req1", resp="resp1", metric=Metric(score=Score(val=8)))
        exp2 = Experience(req="req2", resp="resp2", metric=Metric(score=Score(val=9)))
        context_builder.exps = [exp1, exp2]

        result = context_builder.format_exps()
        expected = "\n".join(
            [
                f"1. {EXP_TEMPLATE.format(req='req1', resp='resp1', score=8)}",
                f"2. {EXP_TEMPLATE.format(req='req2', resp='resp2', score=9)}",
            ]
        )
        assert result == expected
