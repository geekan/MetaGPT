import pytest
from llama_index import ServiceContext
from llama_index.postprocessor import LLMRerank

from metagpt.rag.rankers.factory import RankerFactory
from metagpt.rag.schema import LLMRankerConfig


class TestRankerFactory:
    @pytest.fixture
    def mock_service_context(self, mocker):
        return mocker.MagicMock(spec=ServiceContext)

    def test_get_rankers_with_no_configs_returns_default_ranker(self, mock_service_context):
        # Setup
        factory = RankerFactory()

        # Execute
        rankers = factory.get_rankers(service_context=mock_service_context)

        # Assertions
        assert len(rankers) == 1
        assert isinstance(rankers[0], LLMRerank)

    def test_get_rankers_with_specific_config_returns_correct_ranker(self, mock_service_context):
        # Setup
        config = LLMRankerConfig(top_n=3)
        factory = RankerFactory()

        # Execute
        rankers = factory.get_rankers(configs=[config], service_context=mock_service_context)

        # Assertions
        assert len(rankers) == 1
        assert isinstance(rankers[0], LLMRerank)
        assert rankers[0].top_n == 3

    def test_get_rankers_with_unknown_config_raises_value_error(self, mocker, mock_service_context):
        # Mock
        mock_config = mocker.MagicMock()  # 使用 MagicMock 来模拟一个未知的配置类型

        # Setup
        factory = RankerFactory()

        # Execute & Assertions
        with pytest.raises(ValueError):
            factory.get_rankers(configs=[mock_config], service_context=mock_service_context)
