#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
from typing import Any, Callable, Coroutine, Optional, Union, overload

from pydantic import BaseModel, ConfigDict, model_validator

from metagpt.configs.browser_config import BrowserConfig
from metagpt.tools import WebBrowserEngineType
from metagpt.utils.parse_html import WebPage


class WebBrowserEngine(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    engine: WebBrowserEngineType = WebBrowserEngineType.PLAYWRIGHT
    run_func: Optional[Callable[..., Coroutine[Any, Any, Union[WebPage, list[WebPage]]]]] = None
    proxy: Optional[str] = None

    @model_validator(mode="after")
    def validate_extra(self):
        data = self.model_dump(exclude={"engine"}, exclude_none=True, exclude_defaults=True)
        if self.model_extra:
            data.update(self.model_extra)
        self._process_extra(**data)
        return self

    def _process_extra(self, **kwargs):
        if self.engine is WebBrowserEngineType.PLAYWRIGHT:
            module = "metagpt.tools.web_browser_engine_playwright"
            run_func = importlib.import_module(module).PlaywrightWrapper(**kwargs).run
        elif self.engine is WebBrowserEngineType.SELENIUM:
            module = "metagpt.tools.web_browser_engine_selenium"
            run_func = importlib.import_module(module).SeleniumWrapper(**kwargs).run
        elif self.engine is WebBrowserEngineType.CUSTOM:
            run_func = self.run_func
        else:
            raise NotImplementedError
        self.run_func = run_func

    @classmethod
    def from_browser_config(cls, config: BrowserConfig, **kwargs):
        data = config.model_dump()
        return cls(**data, **kwargs)

    @overload
    async def run(self, url: str) -> WebPage:
        ...

    @overload
    async def run(self, url: str, *urls: str) -> list[WebPage]:
        ...

    async def run(self, url: str, *urls: str) -> WebPage | list[WebPage]:
        return await self.run_func(url, *urls)
