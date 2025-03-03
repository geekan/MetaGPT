import pytest

from metagpt.config2 import Config
from metagpt.configs.exp_pool_config import (
    ExperiencePoolConfig,
    ExperiencePoolRetrievalType,
)
from metagpt.configs.llm_config import LLMConfig
from metagpt.exp_pool.manager import Experience, ExperienceManager
from metagpt.exp_pool.schema import DEFAULT_SIMILARITY_TOP_K, QueryType


class TestExperienceManager:
    @pytest.fixture
    def mock_config(self):
        return Config(
            llm=LLMConfig(),
            exp_pool=ExperiencePoolConfig(
                enable_write=True, enable_read=True, enabled=True, retrieval_type=ExperiencePoolRetrievalType.BM25
            ),
        )

    @pytest.fixture
    def mock_storage(self, mocker):
        engine = mocker.MagicMock()
        engine.add_objs = mocker.MagicMock()
        engine.aretrieve = mocker.AsyncMock(return_value=[])
        engine.count = mocker.MagicMock(return_value=10)
        return engine

    @pytest.fixture
    def exp_manager(self, mock_config, mock_storage):
        manager = ExperienceManager(config=mock_config)
        manager._storage = mock_storage
        return manager

    def test_storage_property(self, exp_manager, mock_storage):
        assert exp_manager.storage == mock_storage

    def test_storage_property_initialization(self, mocker, mock_config):
        mocker.patch.object(ExperienceManager, "_resolve_storage", return_value=mocker.MagicMock())
        manager = ExperienceManager(config=mock_config)
        assert manager._storage is None
        _ = manager.storage
        assert manager._storage is not None

    def test_create_exp_write_disabled(self, exp_manager, mock_config):
        mock_config.exp_pool.enable_write = False
        exp = Experience(req="test", resp="response")
        exp_manager.create_exp(exp)
        exp_manager.storage.add_objs.assert_not_called()

    def test_create_exp_write_enabled(self, exp_manager):
        exp = Experience(req="test", resp="response")
        exp_manager.create_exp(exp)
        exp_manager.storage.add_objs.assert_called_once_with([exp])
        exp_manager.storage.persist.assert_called_once_with(exp_manager.config.exp_pool.persist_path)

    @pytest.mark.asyncio
    async def test_query_exps_read_disabled(self, exp_manager, mock_config):
        mock_config.exp_pool.enable_read = False
        result = await exp_manager.query_exps("query")
        assert result == []

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

    def test_resolve_storage_bm25(self, mocker, mock_config):
        mock_config.exp_pool.retrieval_type = ExperiencePoolRetrievalType.BM25
        mocker.patch.object(ExperienceManager, "_create_bm25_storage", return_value=mocker.MagicMock())
        manager = ExperienceManager(config=mock_config)
        storage = manager._resolve_storage()
        manager._create_bm25_storage.assert_called_once()
        assert storage is not None

    def test_resolve_storage_chroma(self, mocker, mock_config):
        mock_config.exp_pool.retrieval_type = ExperiencePoolRetrievalType.CHROMA
        mocker.patch.object(ExperienceManager, "_create_chroma_storage", return_value=mocker.MagicMock())
        manager = ExperienceManager(config=mock_config)
        storage = manager._resolve_storage()
        manager._create_chroma_storage.assert_called_once()
        assert storage is not None

    def test_create_bm25_storage(self, mocker, mock_config):
        mocker.patch("metagpt.rag.engines.SimpleEngine.from_objs", return_value=mocker.MagicMock())
        mocker.patch("metagpt.rag.engines.SimpleEngine.from_index", return_value=mocker.MagicMock())
        mocker.patch("metagpt.rag.engines.SimpleEngine.get_obj_nodes", return_value=[])
        mocker.patch("metagpt.rag.engines.SimpleEngine._resolve_embed_model", return_value=mocker.MagicMock())
        mocker.patch("llama_index.core.VectorStoreIndex", return_value=mocker.MagicMock())
        mocker.patch("metagpt.rag.schema.BM25RetrieverConfig", return_value=mocker.MagicMock())
        mocker.patch("pathlib.Path.exists", return_value=False)

        manager = ExperienceManager(config=mock_config)
        storage = manager._create_bm25_storage()
        assert storage is not None

    def test_create_chroma_storage(self, mocker, mock_config):
        mocker.patch("metagpt.rag.engines.SimpleEngine.from_objs", return_value=mocker.MagicMock())
        manager = ExperienceManager(config=mock_config)
        storage = manager._create_chroma_storage()
        assert storage is not None

    def test_get_ranker_configs_use_llm_ranker_true(self, mock_config):
        mock_config.exp_pool.use_llm_ranker = True
        manager = ExperienceManager(config=mock_config)
        ranker_configs = manager._get_ranker_configs()
        assert len(ranker_configs) == 1
        assert ranker_configs[0].top_n == DEFAULT_SIMILARITY_TOP_K

    def test_get_ranker_configs_use_llm_ranker_false(self, mock_config):
        mock_config.exp_pool.use_llm_ranker = False
        manager = ExperienceManager(config=mock_config)
        ranker_configs = manager._get_ranker_configs()
        assert len(ranker_configs) == 0
