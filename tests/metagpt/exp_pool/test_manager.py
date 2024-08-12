import pytest

from metagpt.config2 import Config
from metagpt.configs.exp_pool_config import ExperiencePoolConfig
from metagpt.configs.llm_config import LLMConfig
from metagpt.exp_pool.manager import Experience, ExperienceManager
from metagpt.exp_pool.schema import QueryType


class TestExperienceManager:
    @pytest.fixture
    def mock_config(self):
        return Config(llm=LLMConfig(), exp_pool=ExperiencePoolConfig(enable_write=True, enable_read=True, enabled=True))

    @pytest.fixture
    def mock_storage(self, mocker):
        engine = mocker.MagicMock()
        engine.add_objs = mocker.MagicMock()
        engine.aretrieve = mocker.AsyncMock(return_value=[])
        engine._retriever = mocker.MagicMock()
        engine._retriever._vector_store = mocker.MagicMock()
        engine._retriever._vector_store._collection = mocker.MagicMock()
        engine._retriever._vector_store._collection.count = mocker.MagicMock(return_value=10)
        return engine

    @pytest.fixture
    def exp_manager(self, mock_config, mock_storage):
        manager = ExperienceManager(config=mock_config)
        manager._storage = mock_storage
        return manager

    def test_vector_store_property(self, exp_manager):
        assert exp_manager.vector_store == exp_manager.storage._retriever._vector_store

    @pytest.mark.asyncio
    async def test_query_exps_with_exact_match(self, exp_manager, mocker):
        req = "exact query"
        exp1 = Experience(req=req, resp="response1")
        exp2 = Experience(req="different query", resp="response2")

        mock_node1 = mocker.MagicMock(metadata={"obj": exp1})
        mock_node2 = mocker.MagicMock(metadata={"obj": exp2})

        exp_manager.storage.aretrieve.return_value = [mock_node1, mock_node2]

        result = await exp_manager.query_exps(req, query_type=QueryType.EXACT)
        assert len(result) == 1
        assert result[0].req == req

    @pytest.mark.asyncio
    async def test_query_exps_with_tag_filter(self, exp_manager, mocker):
        tag = "test_tag"
        exp1 = Experience(req="query1", resp="response1", tag=tag)
        exp2 = Experience(req="query2", resp="response2", tag="other_tag")

        mock_node1 = mocker.MagicMock(metadata={"obj": exp1})
        mock_node2 = mocker.MagicMock(metadata={"obj": exp2})

        exp_manager.storage.aretrieve.return_value = [mock_node1, mock_node2]

        result = await exp_manager.query_exps("query", tag=tag)
        assert len(result) == 1
        assert result[0].tag == tag

    def test_get_exps_count(self, exp_manager):
        assert exp_manager.get_exps_count() == 10

    def test_create_exp_write_disabled(self, exp_manager, mock_config):
        mock_config.exp_pool.enable_write = False
        exp = Experience(req="test", resp="response")
        exp_manager.create_exp(exp)
        exp_manager.storage.add_objs.assert_not_called()

    @pytest.mark.asyncio
    async def test_query_exps_read_disabled(self, exp_manager, mock_config):
        mock_config.exp_pool.enable_read = False
        result = await exp_manager.query_exps("query")
        assert result == []
