import asyncio

import pytest

from metagpt.exp_pool.decorator import ExpCacheHandler
from metagpt.exp_pool.manager import ExperienceManager
from metagpt.exp_pool.schema import Experience, QueryType, Score
from metagpt.exp_pool.scorers import SimpleScorer
from metagpt.rag.engines import SimpleEngine


class TestExpCache:
    @pytest.fixture
    def mock_func(self, mocker):
        return mocker.AsyncMock()

    @pytest.fixture
    def mock_exp_manager(self, mocker):
        manager = mocker.MagicMock(spec=ExperienceManager)
        manager.storage = mocker.MagicMock(spec=SimpleEngine)
        manager.query_exps = mocker.AsyncMock()
        manager.create_exp = mocker.MagicMock()
        manager.extract_one_perfect_exp = mocker.MagicMock()
        return manager

    @pytest.fixture
    def mock_scorer(self, mocker):
        scorer = mocker.MagicMock(spec=SimpleScorer)
        scorer.evaluate = mocker.AsyncMock()
        return scorer

    @pytest.fixture
    def exp_cache_handler(self, mock_func, mock_exp_manager, mock_scorer):
        return ExpCacheHandler(
            func=mock_func, args=(), kwargs={}, exp_manager=mock_exp_manager, exp_scorer=mock_scorer, pass_exps=False
        )

    @pytest.mark.asyncio
    async def test_fetch_experiences(self, exp_cache_handler, mock_exp_manager):
        await exp_cache_handler.fetch_experiences(QueryType.SEMANTIC)
        mock_exp_manager.query_exps.assert_called_once()

    @pytest.mark.asyncio
    async def test_perfect_experience_found(self, exp_cache_handler, mock_exp_manager, mock_func):
        # Setup: Assume perfect experience is found
        perfect_exp = Experience(req="req", resp="resp")
        mock_exp_manager.extract_one_perfect_exp.return_value = perfect_exp

        # Execute
        exp_cache_handler._exps = [perfect_exp]  # Simulate fetched experiences
        result = exp_cache_handler.get_one_perfect_experience()

        # Assert
        assert result.resp == "resp"
        mock_func.assert_not_called()  # Function should not be called

    @pytest.mark.asyncio
    async def test_execute_function_when_no_perfect_exp(self, exp_cache_handler, mock_exp_manager, mock_func):
        # Setup: No perfect experience
        mock_exp_manager.extract_one_perfect_exp.return_value = None
        mock_func.return_value = "Computed result"

        # Execute
        await exp_cache_handler.execute_function()

        # Assert
        assert exp_cache_handler._result == "Computed result"
        mock_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_and_save_experience(self, exp_cache_handler, mock_scorer, mock_exp_manager):
        # Setup
        mock_scorer.evaluate.return_value = Score(value=100)
        exp_cache_handler._result = "Computed result"

        # Execute
        await exp_cache_handler.evaluate_experience()
        exp_cache_handler.save_experience()

        # Assert
        mock_scorer.evaluate.assert_called_once()
        mock_exp_manager.create_exp.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_function_execution_with_exps(self, exp_cache_handler, mock_exp_manager, mock_func):
        # Setup
        exp_cache_handler.pass_exps = True
        mock_func.return_value = "Async result with exps"
        mock_exp_manager.extract_one_perfect_exp.return_value = None
        exp_cache_handler._exps = [Experience(req="req", resp="resp")]

        # Execute
        await exp_cache_handler.execute_function()

        # Assert
        mock_func.assert_called_once_with(exps=exp_cache_handler._exps)
        assert exp_cache_handler._result == "Async result with exps"

    def test_sync_function_execution_with_exps(self, mocker, exp_cache_handler, mock_exp_manager, mock_func):
        # Setup
        exp_cache_handler.func = mocker.Mock(return_value="Sync result with exps")
        exp_cache_handler.pass_exps = True
        mock_exp_manager.extract_one_perfect_exp.return_value = None
        exp_cache_handler._exps = [Experience(req="req", resp="resp")]

        # Execute
        asyncio.get_event_loop().run_until_complete(exp_cache_handler.execute_function())

        # Assert
        exp_cache_handler.func.assert_called_once_with(exps=exp_cache_handler._exps)
        assert exp_cache_handler._result == "Sync result with exps"

    def test_wrapper_selection_async(self, mocker, exp_cache_handler, mock_func):
        # Setup
        mock_func = mocker.AsyncMock()

        # Execute
        wrapper = ExpCacheHandler.choose_wrapper(mock_func, exp_cache_handler.execute_function)

        # Assert
        assert asyncio.iscoroutinefunction(wrapper), "Wrapper should be asynchronous"

    def test_wrapper_selection_sync(self, exp_cache_handler, mocker):
        # Setup
        sync_func = mocker.Mock()

        # Execute
        wrapper = ExpCacheHandler.choose_wrapper(sync_func, exp_cache_handler.execute_function)

        # Assert
        assert not asyncio.iscoroutinefunction(wrapper), "Wrapper should be synchronous"

    @pytest.mark.asyncio
    async def test_generate_req_identifier(self, exp_cache_handler):
        # Setup
        exp_cache_handler.func = lambda x: x
        exp_cache_handler.args = (42,)
        exp_cache_handler.kwargs = {"y": 3.14}

        # Execute
        req_id = exp_cache_handler.generate_req_identifier()

        # Assert
        expected_id = "<lambda>_(42,)_{'y': 3.14}"
        assert req_id == expected_id, "Request identifier should match the expected format"
