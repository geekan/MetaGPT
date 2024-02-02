#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/6 20:15
@Author  : alexanderwu
@File    : search_engine.py
"""
import importlib
from typing import Callable, Coroutine, Literal, Optional, Union, overload

from pydantic import BaseModel, ConfigDict, model_validator
from semantic_kernel.skill_definition import sk_function

from metagpt.configs.search_config import SearchConfig
from metagpt.logs import logger
from metagpt.tools import SearchEngineType


class SkSearchEngine:
    """A search engine class for executing searches.

    Attributes:
        search_engine: The search engine instance used for executing searches.
    """

    def __init__(self, **kwargs):
        self.search_engine = SearchEngine(**kwargs)

    @sk_function(
        description="searches results from Google. Useful when you need to find short "
        "and succinct answers about a specific topic. Input should be a search query.",
        name="searchAsync",
        input_description="search",
    )
    async def run(self, query: str) -> str:
        result = await self.search_engine.run(query)
        return result


class SearchEngine(BaseModel):
    """A model for configuring and executing searches with different search engines.

    Attributes:
        model_config: Configuration for the model allowing arbitrary types.
        engine: The type of search engine to use.
        run_func: An optional callable for running the search. If not provided, it will be determined based on the engine.
        api_key: An optional API key for the search engine.
        proxy: An optional proxy for the search engine requests.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    engine: SearchEngineType = SearchEngineType.SERPER_GOOGLE
    run_func: Optional[Callable[[str, int, bool], Coroutine[None, None, Union[str, list[str]]]]] = None
    api_key: Optional[str] = None
    proxy: Optional[str] = None

    @model_validator(mode="after")
    def validate_extra(self):
        """Validates extra fields provided to the model and updates the run function accordingly."""
        data = self.model_dump(exclude={"engine"}, exclude_none=True, exclude_defaults=True)
        if self.model_extra:
            data.update(self.model_extra)
        self._process_extra(**data)
        return self

    def _process_extra(
        self,
        run_func: Optional[Callable[[str, int, bool], Coroutine[None, None, Union[str, list[str]]]]] = None,
        **kwargs,
    ):
        """Processes extra configuration and updates the run function based on the search engine type.

        Args:
            run_func: An optional callable for running the search. If not provided, it will be determined based on the engine.
        """
        if self.engine == SearchEngineType.SERPAPI_GOOGLE:
            module = "metagpt.tools.search_engine_serpapi"
            run_func = importlib.import_module(module).SerpAPIWrapper(**kwargs).run
        elif self.engine == SearchEngineType.SERPER_GOOGLE:
            module = "metagpt.tools.search_engine_serper"
            run_func = importlib.import_module(module).SerperWrapper(**kwargs).run
        elif self.engine == SearchEngineType.DIRECT_GOOGLE:
            module = "metagpt.tools.search_engine_googleapi"
            run_func = importlib.import_module(module).GoogleAPIWrapper(**kwargs).run
        elif self.engine == SearchEngineType.DUCK_DUCK_GO:
            module = "metagpt.tools.search_engine_ddg"
            run_func = importlib.import_module(module).DDGAPIWrapper(**kwargs).run
        elif self.engine == SearchEngineType.CUSTOM_ENGINE:
            run_func = self.run_func
        else:
            raise NotImplementedError
        self.run_func = run_func

    @classmethod
    def from_search_config(cls, config: SearchConfig, **kwargs):
        """Creates a SearchEngine instance from a SearchConfig.

        Args:
            config: The search configuration to use for creating the SearchEngine instance.
        """
        data = config.model_dump(exclude={"api_type", "search_func"})
        if config.search_func is not None:
            data["run_func"] = config.search_func

        return cls(engine=config.api_type, **data, **kwargs)

    @classmethod
    def from_search_func(
        cls, search_func: Callable[[str, int, bool], Coroutine[None, None, Union[str, list[str]]]], **kwargs
    ):
        """Creates a SearchEngine instance from a custom search function.

        Args:
            search_func: A callable that executes the search.
        """
        return cls(engine=SearchEngineType.CUSTOM_ENGINE, run_func=search_func, **kwargs)

    @overload
    def run(
        self,
        query: str,
        max_results: int = 8,
        as_string: Literal[True] = True,
    ) -> str:
        ...

    @overload
    def run(
        self,
        query: str,
        max_results: int = 8,
        as_string: Literal[False] = False,
    ) -> list[dict[str, str]]:
        ...

    async def run(
        self,
        query: str,
        max_results: int = 8,
        as_string: bool = True,
        ignore_errors: bool = False,
    ) -> Union[str, list[dict[str, str]]]:
        """Run a search query.

        Args:
            query: The search query.
            max_results: The maximum number of results to return. Defaults to 8.
            as_string: Whether to return the results as a string or a list of dictionaries. Defaults to True.
            ignore_errors: Whether to ignore errors during the search. Defaults to False.

        Returns:
            The search results as a string or a list of dictionaries.
        """
        try:
            return await self.run_func(query, max_results=max_results, as_string=as_string)
        except Exception as e:
            # Handle errors in the API call
            logger.exception(f"fail to search {query} for {e}")
            if not ignore_errors:
                raise e
            return "" if as_string else []
