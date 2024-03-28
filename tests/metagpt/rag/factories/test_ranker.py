import contextlib

import pytest
from llama_index.core.llms import MockLLM
from llama_index.core.postprocessor import LLMRerank

from metagpt.rag.factories.ranker import RankerFactory
from metagpt.rag.schema import ColbertRerankConfig, LLMRankerConfig, ObjectRankerConfig


class TestRankerFactory:
    @pytest.fixture(autouse=True)
    def ranker_factory(self):
        self.ranker_factory: RankerFactory = RankerFactory()

    @pytest.fixture
    def mock_llm(self):
        return MockLLM()

    def test_get_rankers_with_no_configs(self, mock_llm, mocker):
        mocker.patch.object(self.ranker_factory, "_extract_llm", return_value=mock_llm)
        default_rankers = self.ranker_factory.get_rankers()
        assert len(default_rankers) == 0

    def test_get_rankers_with_configs(self, mock_llm):
        mock_config = LLMRankerConfig(llm=mock_llm)
        rankers = self.ranker_factory.get_rankers(configs=[mock_config])
        assert len(rankers) == 1
        assert isinstance(rankers[0], LLMRerank)

    def test_extract_llm_from_config(self, mock_llm):
        mock_config = LLMRankerConfig(llm=mock_llm)
        extracted_llm = self.ranker_factory._extract_llm(config=mock_config)
        assert extracted_llm == mock_llm

    def test_extract_llm_from_kwargs(self, mock_llm):
        extracted_llm = self.ranker_factory._extract_llm(llm=mock_llm)
        assert extracted_llm == mock_llm

    def test_create_llm_ranker(self, mock_llm):
        mock_config = LLMRankerConfig(llm=mock_llm)
        ranker = self.ranker_factory._create_llm_ranker(mock_config)
        assert isinstance(ranker, LLMRerank)

    def test_create_colbert_ranker(self, mocker, mock_llm):
        with contextlib.suppress(ImportError):
            mocker.patch("llama_index.postprocessor.colbert_rerank.ColbertRerank", return_value="colbert")

            mock_config = ColbertRerankConfig(llm=mock_llm)
            ranker = self.ranker_factory._create_colbert_ranker(mock_config)

            assert ranker == "colbert"

    def test_create_object_ranker(self, mocker, mock_llm):
        mocker.patch("metagpt.rag.factories.ranker.ObjectSortPostprocessor", return_value="object")

        mock_config = ObjectRankerConfig(field_name="fake", llm=mock_llm)
        ranker = self.ranker_factory._create_object_ranker(mock_config)

        assert ranker == "object"
