import pytest

from metagpt.exp_pool.perfect_judges import SimplePerfectJudge
from metagpt.exp_pool.schema import MAX_SCORE, Experience, Metric, Score


class TestSimplePerfectJudge:
    @pytest.fixture
    def simple_perfect_judge(self):
        return SimplePerfectJudge()

    @pytest.mark.asyncio
    async def test_is_perfect_exp_perfect_match(self, simple_perfect_judge):
        exp = Experience(req="test_request", resp="resp", metric=Metric(score=Score(val=MAX_SCORE)))
        result = await simple_perfect_judge.is_perfect_exp(exp, "test_request")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_perfect_exp_imperfect_score(self, simple_perfect_judge):
        exp = Experience(req="test_request", resp="resp", metric=Metric(score=Score(val=MAX_SCORE - 1)))
        result = await simple_perfect_judge.is_perfect_exp(exp, "test_request")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_perfect_exp_mismatched_request(self, simple_perfect_judge):
        exp = Experience(req="test_request", resp="resp", metric=Metric(score=Score(val=MAX_SCORE)))
        result = await simple_perfect_judge.is_perfect_exp(exp, "different_request")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_perfect_exp_no_metric(self, simple_perfect_judge):
        exp = Experience(req="test_request", resp="resp")
        result = await simple_perfect_judge.is_perfect_exp(exp, "test_request")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_perfect_exp_no_score(self, simple_perfect_judge):
        exp = Experience(req="test_request", resp="resp", metric=Metric())
        result = await simple_perfect_judge.is_perfect_exp(exp, "test_request")
        assert result is False
