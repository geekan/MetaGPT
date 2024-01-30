#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import importlib
from typing import Any, Callable, Coroutine, overload

from metagpt.tools import WebBrowserEngineType
from metagpt.utils.parse_html import WebPage


class WebBrowserEngine:
    """A class to represent a web browser engine.

    This class abstracts away the details of using different web browser engines like Playwright, Selenium, or a custom engine
    to fetch web pages.

    Attributes:
        run_func: A callable that when executed returns a Coroutine which fetches a web page or a list of web pages.
        engine: The type of web browser engine being used.

    Args:
        engine: The type of web browser engine to use. Defaults to WebBrowserEngineType.PLAYWRIGHT.
        run_func: An optional callable that defines how to run the web browser engine. If not provided, it is determined
                  based on the engine type.
    """

    def __init__(
        self,
        engine: WebBrowserEngineType = WebBrowserEngineType.PLAYWRIGHT,
        run_func: Callable[..., Coroutine[Any, Any, WebPage | list[WebPage]]] | None = None,
    ):
        if engine is None:
            raise NotImplementedError

        if WebBrowserEngineType(engine) is WebBrowserEngineType.PLAYWRIGHT:
            module = "metagpt.tools.web_browser_engine_playwright"
            run_func = importlib.import_module(module).PlaywrightWrapper().run
        elif WebBrowserEngineType(engine) is WebBrowserEngineType.SELENIUM:
            module = "metagpt.tools.web_browser_engine_selenium"
            run_func = importlib.import_module(module).SeleniumWrapper().run
        elif WebBrowserEngineType(engine) is WebBrowserEngineType.CUSTOM:
            run_func = run_func
        else:
            raise NotImplementedError
        self.run_func = run_func
        self.engine = engine

    @overload
    async def run(self, url: str) -> WebPage:
        ...

    @overload
    async def run(self, url: str, *urls: str) -> list[WebPage]:
        ...

    async def run(self, url: str, *urls: str) -> WebPage | list[WebPage]:
        """Fetches one or more web pages.

        This method dynamically decides whether to fetch a single web page or multiple based on the provided arguments.

        Args:
            url: The URL of the web page to fetch. If multiple URLs are provided, this is the first URL.
            *urls: Additional URLs of web pages to fetch.

        Returns:
            A WebPage object if a single URL is provided, or a list of WebPage objects if multiple URLs are provided.
        """
        return await self.run_func(url, *urls)
