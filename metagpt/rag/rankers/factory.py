"""Rankers Factory"""
from llama_index import ServiceContext
from llama_index.postprocessor import LLMRerank
from llama_index.postprocessor.types import BaseNodePostprocessor

from metagpt.rag.schema import LLMRankerConfig, RankerConfigType


class RankerFactory:
    def __init__(self):
        self.ranker_creators = {
            LLMRankerConfig: self._create_llm_ranker,
        }

    def get_rankers(
        self, configs: list[RankerConfigType] = None, service_context: ServiceContext = None
    ) -> list[BaseNodePostprocessor]:
        if not configs:
            return [self._default_ranker(service_context)]

        return [self._get_ranker(config, service_context) for config in configs]

    def _default_ranker(self, service_context: ServiceContext = None) -> LLMRerank:
        return LLMRerank(top_n=LLMRankerConfig().top_n, service_context=service_context)

    def _get_ranker(self, config: RankerConfigType, service_context: ServiceContext = None) -> BaseNodePostprocessor:
        create_func = self.ranker_creators.get(type(config))
        if create_func:
            return create_func(config, service_context)

        raise ValueError(f"Unknown ranker config: {config}")

    def _create_llm_ranker(self, config: LLMRankerConfig, service_context=None) -> LLMRerank:
        return LLMRerank(**config.model_dump(), service_context=service_context)


get_rankers = RankerFactory().get_rankers
