import asyncio

import pytest

from metagpt.config2 import Config
from metagpt.configs.exp_pool_config import ExperiencePoolConfig
from metagpt.exp_pool.context_builders import SimpleContextBuilder
from metagpt.exp_pool.decorator import ExpCacheHandler, exp_cache
from metagpt.exp_pool.manager import ExperienceManager
from metagpt.exp_pool.perfect_judges import SimplePerfectJudge
from metagpt.exp_pool.schema import Experience, QueryType, Score
from metagpt.exp_pool.scorers import SimpleScorer
from metagpt.rag.engines import SimpleEngine


class TestExpCacheHandler:
    @pytest.fixture
    def mock_func(self, mocker):
        return mocker.AsyncMock()

    @pytest.fixture
    def mock_exp_manager(self, mocker):
        manager = mocker.MagicMock(spec=ExperienceManager)
        manager.storage = mocker.MagicMock(spec=SimpleEngine)
        manager.config = mocker.MagicMock(spec=Config)
        manager.config.exp_pool = ExperiencePoolConfig()
        manager.query_exps = mocker.AsyncMock()
        manager.create_exp = mocker.MagicMock()
        return manager

    @pytest.fixture
    def mock_scorer(self, mocker):
        scorer = mocker.MagicMock(spec=SimpleScorer)
        scorer.evaluate = mocker.AsyncMock()
        return scorer

    @pytest.fixture
    def mock_perfect_judge(self, mocker):
        return mocker.MagicMock(spec=SimplePerfectJudge)

    @pytest.fixture
    def mock_context_builder(self, mocker):
        return mocker.MagicMock(spec=SimpleContextBuilder)

    @pytest.fixture
    def exp_cache_handler(self, mock_func, mock_exp_manager, mock_scorer, mock_perfect_judge, mock_context_builder):
        return ExpCacheHandler(
            func=mock_func,
            args=(),
            kwargs={"req": "test_req"},
            exp_manager=mock_exp_manager,
            exp_scorer=mock_scorer,
            exp_perfect_judge=mock_perfect_judge,
            context_builder=mock_context_builder,
        )

    @pytest.mark.asyncio
    async def test_fetch_experiences(self, exp_cache_handler, mock_exp_manager):
        mock_exp_manager.query_exps.return_value = [Experience(req="test_req", resp="test_resp")]
        await exp_cache_handler.fetch_experiences()
        mock_exp_manager.query_exps.assert_called_once_with(
            "test_req", query_type=QueryType.SEMANTIC, tag=exp_cache_handler.tag
        )
        assert len(exp_cache_handler._exps) == 1

    @pytest.mark.asyncio
    async def test_get_one_perfect_exp(self, exp_cache_handler, mock_perfect_judge):
        exp = Experience(req="test_req", resp="perfect_resp")
        exp_cache_handler._exps = [exp]
        mock_perfect_judge.is_perfect_exp.return_value = True
        result = await exp_cache_handler.get_one_perfect_exp()
        assert result == "perfect_resp"

    @pytest.mark.asyncio
    async def test_execute_function(self, exp_cache_handler, mock_func, mock_context_builder):
        mock_context_builder.build.return_value = "built_context"
        mock_func.return_value = "function_result"
        await exp_cache_handler.execute_function()
        mock_context_builder.build.assert_called_once()
        mock_func.assert_called_once_with(req="built_context")
        assert exp_cache_handler._raw_resp == "function_result"
        assert exp_cache_handler._resp == "function_result"

    @pytest.mark.asyncio
    async def test_process_experience(self, exp_cache_handler, mock_scorer, mock_exp_manager):
        exp_cache_handler._resp = "test_resp"
        mock_scorer.evaluate.return_value = Score(val=8)
        await exp_cache_handler.process_experience()
        mock_scorer.evaluate.assert_called_once()
        mock_exp_manager.create_exp.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_experience(self, exp_cache_handler, mock_scorer):
        exp_cache_handler._resp = "test_resp"
        mock_scorer.evaluate.return_value = Score(val=9)
        await exp_cache_handler.evaluate_experience()
        assert exp_cache_handler._score.val == 9

    def test_save_experience(self, exp_cache_handler, mock_exp_manager):
        exp_cache_handler._req = "test_req"
        exp_cache_handler._resp = "test_resp"
        exp_cache_handler._score = Score(val=7)
        exp_cache_handler.save_experience()
        mock_exp_manager.create_exp.assert_called_once()

    def test_choose_wrapper_async(self, mocker):
        async def async_func():
            pass

        wrapper = ExpCacheHandler.choose_wrapper(async_func, mocker.AsyncMock())
        assert asyncio.iscoroutinefunction(wrapper)

    def test_choose_wrapper_sync(self, mocker):
        def sync_func():
            pass

        wrapper = ExpCacheHandler.choose_wrapper(sync_func, mocker.AsyncMock())
        assert not asyncio.iscoroutinefunction(wrapper)

    def test_validate_params(self):
        with pytest.raises(ValueError):
            ExpCacheHandler(func=lambda x: x, args=(), kwargs={})

    def test_generate_tag(self):
        class TestClass:
            def test_method(self):
                pass

        handler = ExpCacheHandler(func=TestClass().test_method, args=(TestClass(),), kwargs={"req": "test"})
        assert handler._generate_tag() == "TestClass.test_method"

        handler = ExpCacheHandler(func=lambda x: x, args=(), kwargs={"req": "test"})
        assert handler._generate_tag() == "<lambda>"


class TestExpCache:
    @pytest.fixture
    def mock_exp_manager(self, mocker, mock_config):
        manager = mocker.MagicMock(spec=ExperienceManager)
        manager.storage = mocker.MagicMock(spec=SimpleEngine)
        manager.config = mock_config
        manager.query_exps = mocker.AsyncMock()
        manager.create_exp = mocker.MagicMock()
        return manager

    @pytest.fixture
    def mock_scorer(self, mocker):
        scorer = mocker.MagicMock(spec=SimpleScorer)
        scorer.evaluate = mocker.AsyncMock(return_value=Score())
        return scorer

    @pytest.fixture
    def mock_perfect_judge(self, mocker):
        return mocker.MagicMock(spec=SimplePerfectJudge)

    @pytest.fixture
    def mock_config(self, mocker):
        config = Config.default().model_copy(deep=True)
        default = mocker.patch("metagpt.config2.Config.default")
        default.return_value = config
        return config

    @pytest.mark.asyncio
    async def test_exp_cache_disabled(self, mock_config, mock_exp_manager):
        mock_config.exp_pool.enabled = False

        @exp_cache(manager=mock_exp_manager)
        async def test_func(req):
            return "result"

        result = await test_func(req="test")
        assert result == "result"
        mock_exp_manager.query_exps.assert_not_called()

    @pytest.mark.asyncio
    async def test_exp_cache_enabled_no_perfect_exp(self, mock_config, mock_exp_manager, mock_scorer):
        mock_config.exp_pool.enabled = True
        mock_config.exp_pool.enable_read = True
        mock_config.exp_pool.enable_write = True
        mock_exp_manager.query_exps.return_value = []

        @exp_cache(manager=mock_exp_manager, scorer=mock_scorer)
        async def test_func(req):
            return "computed_result"

        result = await test_func(req="test")
        assert result == "computed_result"
        mock_exp_manager.query_exps.assert_called()
        mock_exp_manager.create_exp.assert_called()

    @pytest.mark.asyncio
    async def test_exp_cache_enabled_with_perfect_exp(self, mock_config, mock_exp_manager, mock_perfect_judge):
        mock_config.exp_pool.enabled = True
        mock_config.exp_pool.enable_read = True
        perfect_exp = Experience(req="test", resp="perfect_result")
        mock_exp_manager.query_exps.return_value = [perfect_exp]
        mock_perfect_judge.is_perfect_exp.return_value = True

        @exp_cache(manager=mock_exp_manager, perfect_judge=mock_perfect_judge)
        async def test_func(req):
            return "should_not_be_called"

        result = await test_func(req="test")
        assert result == "perfect_result"
        mock_exp_manager.query_exps.assert_called_once()
        mock_exp_manager.create_exp.assert_not_called()
