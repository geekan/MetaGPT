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
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    engine: SearchEngineType = SearchEngineType.SERPER_GOOGLE
    run_func: Optional[Callable[[str, int, bool], Coroutine[None, None, Union[str, list[str]]]]] = None
    api_key: Optional[str] = None
    proxy: Optional[str] = None

    @model_validator(mode="after")
    def validate_extra(self):
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
        data = config.model_dump(exclude={"api_type", "search_func"})
        if config.search_func is not None:
            data["run_func"] = config.search_func

        return cls(engine=config.api_type, **data, **kwargs)

    @classmethod
    def from_search_func(
        cls, search_func: Callable[[str, int, bool], Coroutine[None, None, Union[str, list[str]]]], **kwargs
    ):
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
