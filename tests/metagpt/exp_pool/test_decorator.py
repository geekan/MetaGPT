import asyncio
import inspect

import pytest

from metagpt.exp_pool.decorator import ExpCacheHandler, exp_cache
from metagpt.exp_pool.manager import ExperienceManager
from metagpt.exp_pool.schema import Experience, QueryType, Score
from metagpt.exp_pool.scorers import SimpleScorer
from metagpt.rag.engines import SimpleEngine


def for_test_function(a, b, c=None):
    return a + b if c is None else a + b + c


class ForTestClass:
    def for_test_method(self, x, y):
        return x * y

    @classmethod
    def for_test_class_method(cls, x, y):
        return x**y


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

        # Exec
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

        # Exec
        await exp_cache_handler.execute_function()

        # Assert
        assert exp_cache_handler._result == "Computed result"
        mock_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_and_save_experience(self, exp_cache_handler, mock_scorer, mock_exp_manager):
        # Setup
        mock_scorer.evaluate.return_value = Score(value=100)
        exp_cache_handler._result = "Computed result"

        # Exec
        await exp_cache_handler.evaluate_experience()
        exp_cache_handler.save_experience()

        # Assert
        mock_scorer.evaluate.assert_called_once()
        mock_exp_manager.create_exp.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_function_execution_with_exps(self, exp_cache_handler, mock_exp_manager, mock_func):
        # Setup
        exp_cache_handler.pass_exps_to_func = True
        mock_func.return_value = "Async result with exps"
        mock_exp_manager.extract_one_perfect_exp.return_value = None
        exp_cache_handler._exps = [Experience(req="req", resp="resp")]

        # Exec
        await exp_cache_handler.execute_function()

        # Assert
        mock_func.assert_called_once_with(exps=exp_cache_handler._exps)
        assert exp_cache_handler._result == "Async result with exps"

    def test_sync_function_execution_with_exps(self, mocker, exp_cache_handler, mock_exp_manager, mock_func):
        # Setup
        exp_cache_handler.func = mocker.Mock(return_value="Sync result with exps")
        exp_cache_handler.pass_exps_to_func = True
        mock_exp_manager.extract_one_perfect_exp.return_value = None
        exp_cache_handler._exps = [Experience(req="req", resp="resp")]

        # Exec
        asyncio.get_event_loop().run_until_complete(exp_cache_handler.execute_function())

        # Assert
        exp_cache_handler.func.assert_called_once_with(exps=exp_cache_handler._exps)
        assert exp_cache_handler._result == "Sync result with exps"

    def test_wrapper_selection_async(self, mocker, exp_cache_handler, mock_func):
        # Setup
        mock_func = mocker.AsyncMock()

        # Exec
        wrapper = ExpCacheHandler.choose_wrapper(mock_func, exp_cache_handler.execute_function)

        # Assert
        assert asyncio.iscoroutinefunction(wrapper), "Wrapper should be asynchronous"

    def test_wrapper_selection_sync(self, exp_cache_handler, mocker):
        # Setup
        sync_func = mocker.Mock()

        # Exec
        wrapper = ExpCacheHandler.choose_wrapper(sync_func, exp_cache_handler.execute_function)

        # Assert
        assert not asyncio.iscoroutinefunction(wrapper), "Wrapper should be synchronous"

    @pytest.mark.parametrize(
        "func, args, kwargs, expected",
        [
            (for_test_function, (1, 2), {"c": 3}, 'for_test_function@[1~2]@{"c"!3}'),
            (ForTestClass().for_test_method, (4, 5), {}, "ForTestClass.for_test_method@[4~5]@{}"),
            (ForTestClass.for_test_class_method, (6, 7), {}, "ForTestClass.for_test_class_method@[6~7]@{}"),
            (for_test_function, (), {}, "for_test_function@[]@{}"),
            (
                for_test_function,
                ("hello", [1, 2]),
                {"key": "value"},
                'for_test_function@["hello"~[1~2]]@{"key"!"value"}',
            ),
        ],
    )
    def test_generate_req_identifier(self, func, args, kwargs, expected):
        req_identifier = ExpCacheHandler.generate_req_identifier(func, *args, **kwargs)
        assert req_identifier == expected

    @pytest.mark.asyncio
    async def test_exp_cache_with_perfect_experience(self, mocker, mock_exp_manager):
        # Mock perfect experience
        perfect_exp = Experience(req="test_req", resp="perfect_response")
        mock_exp_manager.query_exps = mocker.AsyncMock(return_value=[perfect_exp])
        mock_exp_manager.extract_one_perfect_exp = mocker.MagicMock(return_value=perfect_exp)
        async_mock_func = mocker.AsyncMock()

        # Setup
        decorated_func = exp_cache(async_mock_func, manager=mock_exp_manager)

        # Exec
        result: Experience = await decorated_func()

        # Assert
        assert result.resp == "perfect_response", "Should return the perfect experience response"
        async_mock_func.assert_not_called()

    @pytest.mark.asyncio
    async def test_exp_cache_without_perfect_experience(self, mocker, mock_exp_manager):
        # Mock
        mock_exp_manager.query_exps = mocker.AsyncMock(return_value=[])
        mock_exp_manager.extract_one_perfect_exp = mocker.MagicMock(return_value=None)
        async_mock_func = mocker.AsyncMock(return_value="computed_response")
        async_mock_func.__signature__ = inspect.signature(for_test_function)

        # Setup
        decorated_func = exp_cache(async_mock_func, manager=mock_exp_manager)

        # Exec
        result = await decorated_func()

        # Assert
        assert result == "computed_response", "Should execute and return the function's response"
        async_mock_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_exp_cache_saves_new_experience(self, mocker, mock_exp_manager, mock_scorer):
        # Mock
        mock_exp_manager.query_exps = mocker.AsyncMock(return_value=[])
        mock_exp_manager.extract_one_perfect_exp = mocker.MagicMock(return_value=None)
        async_mock_func = mocker.AsyncMock(return_value="computed_response")
        mock_scorer.evaluate = mocker.AsyncMock(return_value=Score(value=100))

        # Setup
        decorated_func = exp_cache(async_mock_func, manager=mock_exp_manager, scorer=mock_scorer)

        # Exec
        await decorated_func()

        # Assert
        mock_exp_manager.create_exp.assert_called_once()
