#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/6 20:15
@Author  : alexanderwu
@File    : search_engine.py
"""
import importlib
from typing import Callable, Coroutine, Literal, overload, Optional, Union

from pydantic import BaseModel, root_validator, ValidationError, validator

from semantic_kernel.skill_definition import sk_function

from metagpt.config import CONFIG
from metagpt.tools import SearchEngineType


class SkSearchEngine:
    def __init__(self):
        self.search_engine = SearchEngine()

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
    """Class representing a search engine.

    Args:
        engine: The search engine type. Defaults to the search engine specified in the config.
        run_func: The function to run the search. Defaults to None.

    Attributes:
        run_func: The function to run the search.
        engine: The search engine type.
    """
    engine:SearchEngineType
    run_func: Callable[[str, int, bool], Coroutine[None, None, Union[str, list[str]]]] = None

    @root_validator
    def validate_engine_and_run_func(cls, values):
        engine = values.get('engine')
        run_func = values.get('run_func')
        # values = {}
        # 对 engine 属性进行验证和处理
        if engine is None:
            raise ValidationError('engine cannot be None')
    
        if engine == SearchEngineType.SERPAPI_GOOGLE:
            module = "metagpt.tools.search_engine_serpapi"
            run_func = importlib.import_module(module).SerpAPIWrapper().run
        elif engine == SearchEngineType.SERPER_GOOGLE:
            module = "metagpt.tools.search_engine_serper"
            run_func = importlib.import_module(module).SerperWrapper().run
        elif engine == SearchEngineType.DIRECT_GOOGLE:
            module = "metagpt.tools.search_engine_googleapi"
            run_func = importlib.import_module(module).GoogleAPIWrapper().run
        elif engine == SearchEngineType.DUCK_DUCK_GO:
            module = "metagpt.tools.search_engine_ddg"
            run_func = importlib.import_module(module).DDGAPIWrapper().run
        elif engine == SearchEngineType.CUSTOM_ENGINE:
            # 在这里添加对 custom_engine 的处理逻辑
            pass
        else:
            raise ValidationError('Invalid engine type')
    
        # 将处理后的 run_func 设置回模型
        values['run_func'] = run_func
        return values

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

    async def run(self, query: str, max_results: int = 8, as_string: bool = True) -> Union[str, list[dict[str, str]]]:
        """Run a search query.

        Args:
            query: The search query.
            max_results: The maximum number of results to return. Defaults to 8.
            as_string: Whether to return the results as a string or a list of dictionaries. Defaults to True.

        Returns:
            The search results as a string or a list of dictionaries.
        """
        return await self.run_func(query, max_results=max_results, as_string=as_string)


if __name__ =="__main__":
    # from metagpt.config import Config
    # engine = Config().search_engine
    # print(engine)
    # ss_engine = SearchEngine({"engine":None,
    #                           "run_func":""})
    config_data = {
        'engine': SearchEngineType.SERPAPI_GOOGLE,
        'run_func': None  # 你可以设置一个默认值，或者让 Pydantic 抛出 ValidationError
    }

    # try:
    # search_engine_config = SearchEngine(SearchEngineType.SERPAPI_GOOGLE, None)
    search_engine_config = SearchEngine(**config_data)
    # except ValidationError as e:
    #     print(f"Validation error: {e}")