import pytest
from llama_index.core.llms import LLM
from llama_index.core.postprocessor import LLMRerank

from metagpt.rag.factories.ranker import RankerFactory
from metagpt.rag.schema import LLMRankerConfig


class TestRankerFactory:
    @pytest.fixture
    def ranker_factory(self) -> RankerFactory:
        return RankerFactory()

    @pytest.fixture
    def mock_llm(self, mocker):
        return mocker.MagicMock(spec=LLM)

    def test_get_rankers_with_no_configs(self, ranker_factory: RankerFactory, mock_llm, mocker):
        mocker.patch.object(ranker_factory, "_extract_llm", return_value=mock_llm)
        default_rankers = ranker_factory.get_rankers()
        assert len(default_rankers) == 0

    def test_get_rankers_with_configs(self, ranker_factory: RankerFactory, mock_llm):
        mock_config = LLMRankerConfig(llm=mock_llm)
        rankers = ranker_factory.get_rankers(configs=[mock_config])
        assert len(rankers) == 1
        assert isinstance(rankers[0], LLMRerank)

    def test_create_llm_ranker_creates_correct_instance(self, ranker_factory: RankerFactory, mock_llm):
        mock_config = LLMRankerConfig(llm=mock_llm)
        ranker = ranker_factory._create_llm_ranker(mock_config)
        assert isinstance(ranker, LLMRerank)

    def test_extract_llm_from_config(self, ranker_factory: RankerFactory, mock_llm):
        mock_config = LLMRankerConfig(llm=mock_llm)
        extracted_llm = ranker_factory._extract_llm(config=mock_config)
        assert extracted_llm == mock_llm

    def test_extract_llm_from_kwargs(self, ranker_factory: RankerFactory, mock_llm):
        extracted_llm = ranker_factory._extract_llm(llm=mock_llm)
        assert extracted_llm == mock_llm
