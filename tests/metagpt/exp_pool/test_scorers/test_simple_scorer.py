import pytest

from metagpt.exp_pool.schema import Score
from metagpt.exp_pool.scorers.simple import SIMPLE_SCORER_TEMPLATE, SimpleScorer
from metagpt.llm import BaseLLM


class TestSimpleScorer:
    @pytest.fixture
    def mock_llm(self, mocker):
        mock_llm = mocker.MagicMock(spec=BaseLLM)
        return mock_llm

    @pytest.fixture
    def simple_scorer(self, mock_llm):
        return SimpleScorer(llm=mock_llm)

    def test_init(self, mock_llm):
        scorer = SimpleScorer(llm=mock_llm)
        assert isinstance(scorer.llm, BaseLLM)

    @pytest.mark.asyncio
    async def test_evaluate(self, simple_scorer, mock_llm):
        # Mock function to evaluate
        def mock_func(a, b):
            """This is a mock function."""
            return a + b

        # Mock LLM response
        mock_llm.aask.return_value = '```json\n{"val": 8, "reason": "Good performance"}\n```'

        # Test evaluate method
        result = await simple_scorer.evaluate(mock_func, 5, args=(2, 3), kwargs={})

        # Assert LLM was called with correct prompt
        expected_prompt = SIMPLE_SCORER_TEMPLATE.format(
            func_name=mock_func.__name__,
            func_doc=mock_func.__doc__,
            func_signature="(a, b)",
            func_args=(2, 3),
            func_kwargs={},
            func_result=5,
        )
        mock_llm.aask.assert_called_once_with(expected_prompt)

        # Assert the result is correct
        assert isinstance(result, Score)
        assert result.val == 8
        assert result.reason == "Good performance"
