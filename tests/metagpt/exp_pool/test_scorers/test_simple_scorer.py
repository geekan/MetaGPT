import json

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
    async def test_evaluate(self, simple_scorer, mock_llm, mocker):
        # Mock request and response
        req = "What is the capital of France?"
        resp = "The capital of France is Paris."

        # Mock LLM response
        mock_llm_response = '{"val": 9, "reason": "Accurate and concise answer"}'
        mock_llm.aask.return_value = f"```json\n{mock_llm_response}\n```"

        # Mock CodeParser.parse_code
        mocker.patch("metagpt.utils.common.CodeParser.parse_code", return_value=mock_llm_response)

        # Test evaluate method
        result = await simple_scorer.evaluate(req, resp)

        # Assert LLM was called with correct prompt
        expected_prompt = SIMPLE_SCORER_TEMPLATE.format(req=req, resp=resp)
        mock_llm.aask.assert_called_once_with(expected_prompt)

        # Assert the result is correct
        assert isinstance(result, Score)
        assert result.val == 9
        assert result.reason == "Accurate and concise answer"

    @pytest.mark.asyncio
    async def test_evaluate_invalid_response(self, simple_scorer, mock_llm, mocker):
        # Mock request and response
        req = "What is the capital of France?"
        resp = "The capital of France is Paris."

        # Mock LLM response with invalid JSON
        mock_llm_response = "Invalid JSON"
        mock_llm.aask.return_value = f"```json\n{mock_llm_response}\n```"

        # Mock CodeParser.parse_code
        mocker.patch("metagpt.utils.common.CodeParser.parse_code", return_value=mock_llm_response)

        # Test evaluate method with invalid response
        with pytest.raises(json.JSONDecodeError):
            await simple_scorer.evaluate(req, resp)
