"""init"""
from metagpt.rag.schema import RankerConfig, LLMRankerConfig
from llama_index import ServiceContext
from llama_index.postprocessor import LLMRerank
from llama_index.postprocessor.types import BaseNodePostprocessor


def get_rankers(
    configs: list[RankerConfig] = None, service_context: ServiceContext = None
) -> list[BaseNodePostprocessor]:
    if not configs:
        return [_default_ranker(service_context)]

    return [_get_ranker(config, service_context) for config in configs]


def _default_ranker(service_context: ServiceContext = None):
    return LLMRerank(top_n=LLMRankerConfig().top_n, service_context=service_context)


def _get_ranker(config: RankerConfig, service_context: ServiceContext = None):
    ranker_factory = {
        LLMRankerConfig: _create_llm_ranker,
    }

    create_func = ranker_factory.get(type(config))
    if create_func:
        return create_func(config, service_context)

    raise ValueError(f"Unknown ranker config: {config}")


def _create_llm_ranker(config, service_context=None):
    return LLMRerank(top_n=config.top_n, service_context=service_context)
