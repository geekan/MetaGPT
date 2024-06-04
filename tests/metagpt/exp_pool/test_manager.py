import pytest

from metagpt.config2 import Config
from metagpt.configs.exp_pool_config import ExperiencePoolConfig
from metagpt.configs.llm_config import LLMConfig
from metagpt.exp_pool.manager import ExperienceManager
from metagpt.exp_pool.schema import MAX_SCORE, Experience, Metric
from metagpt.rag.engines import SimpleEngine


class TestExperienceManager:
    @pytest.fixture
    def mock_config(self):
        return Config(llm=LLMConfig(), exp_pool=ExperiencePoolConfig(enable_write=True, enable_read=True))

    @pytest.fixture
    def mock_storage(self, mocker):
        engine = mocker.MagicMock(spec=SimpleEngine)
        engine.add_objs = mocker.MagicMock()
        engine.aretrieve = mocker.AsyncMock(return_value=[])
        return engine

    @pytest.fixture
    def mock_experience_manager(self, mock_config, mock_storage):
        return ExperienceManager(config=mock_config, storage=mock_storage)

    @pytest.fixture
    def mock_experience(self):
        return Experience(req="req", resp="resp")

    def test_initialize_storage(self, mock_experience_manager, mock_storage):
        assert mock_experience_manager.storage is mock_storage

    def test_create_exp(self, mock_experience_manager, mock_experience):
        mock_experience_manager.create_exp(mock_experience)
        mock_experience_manager.storage.add_objs.assert_called_once_with([mock_experience])

    def test_create_exp_write_disabled(self, mock_experience_manager, mock_experience, mock_config):
        mock_config.exp_pool.enable_write = False
        mock_experience_manager.create_exp(mock_experience)
        mock_experience_manager.storage.add_objs.assert_not_called()

    @pytest.mark.asyncio
    async def test_query_exps(self, mock_experience_manager, mocker):
        req = "req"
        resp = "resp"
        tag = "test"
        experiences = [Experience(req=req, resp=resp, tag="test"), Experience(req=req, resp=resp, tag="other")]
        mock_experience_manager.storage.aretrieve.return_value = [
            mocker.MagicMock(metadata={"obj": exp}) for exp in experiences
        ]

        result = await mock_experience_manager.query_exps(req, tag)
        assert len(result) == 1
        assert result[0].tag == "test"

    @pytest.mark.asyncio
    async def test_query_exps_no_read_permission(self, mock_experience_manager, mock_config):
        mock_config.exp_pool.enable_read = False
        result = await mock_experience_manager.query_exps("query")
        assert result == []

    def test_extract_one_perfect_exp(self, mock_experience_manager):
        experiences = [
            Experience(req="req", resp="resp", metric=Metric(score=MAX_SCORE)),
            Experience(req="req", resp="resp"),
        ]
        perfect_exp: Experience = mock_experience_manager.extract_one_perfect_exp(experiences)
        assert perfect_exp is not None
        assert perfect_exp.metric.score == MAX_SCORE

    def test_is_perfect_exp(self):
        exp = Experience(req="req", resp="resp", metric=Metric(score=MAX_SCORE))
        assert ExperienceManager.is_perfect_exp(exp) == True

        exp = Experience(req="req", resp="resp")
        assert ExperienceManager.is_perfect_exp(exp) == False
