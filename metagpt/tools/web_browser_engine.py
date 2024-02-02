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
    """Defines a web browser engine configuration for automated browsing and data extraction.

    This class encapsulates the configuration and operational logic for different web browser engines,
    such as Playwright, Selenium, or custom implementations. It provides a unified interface to run
    browser automation tasks.

    Attributes:
        model_config: Configuration dictionary allowing arbitrary types and extra fields.
        engine: The type of web browser engine to use.
        run_func: An optional coroutine function to run the browser engine.
        proxy: An optional proxy server URL to use with the browser engine.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    engine: WebBrowserEngineType = WebBrowserEngineType.PLAYWRIGHT
    run_func: Optional[Callable[..., Coroutine[Any, Any, Union[WebPage, list[WebPage]]]]] = None
    proxy: Optional[str] = None

    @model_validator(mode="after")
    def validate_extra(self):
        """Validates and processes extra configuration data after model initialization.

        This method is automatically called by Pydantic to validate and process any extra configuration
        data provided to the model. It ensures that the extra data is properly integrated into the model's
        configuration and operational logic.

        Returns:
            The instance itself after processing the extra data.
        """
        data = self.model_dump(exclude={"engine"}, exclude_none=True, exclude_defaults=True)
        if self.model_extra:
            data.update(self.model_extra)
        self._process_extra(**data)
        return self

    def _process_extra(self, **kwargs):
        """Processes extra configuration data to set up the browser engine run function.

        Depending on the specified engine type, this method dynamically imports and configures
        the appropriate browser engine wrapper and its run function.

        Args:
            **kwargs: Arbitrary keyword arguments representing extra configuration data.

        Raises:
            NotImplementedError: If the engine type is not supported.
        """
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
        """Creates a WebBrowserEngine instance from a BrowserConfig object and additional keyword arguments.

        This class method facilitates the creation of a WebBrowserEngine instance by extracting
        configuration data from a BrowserConfig object and optionally merging it with additional
        keyword arguments.

        Args:
            config: A BrowserConfig object containing base configuration data.
            **kwargs: Optional additional keyword arguments to override or extend the configuration.

        Returns:
            A new instance of WebBrowserEngine configured according to the provided arguments.
        """
        data = config.model_dump()
        return cls(**data, **kwargs)

    @overload
    async def run(self, url: str) -> WebPage:
        ...

    @overload
    async def run(self, url: str, *urls: str) -> list[WebPage]:
        ...

    async def run(self, url: str, *urls: str) -> WebPage | list[WebPage]:
        """Runs the browser engine to load one or more web pages.

        This method is the implementation of the overloaded run signatures. It delegates the task
        of loading web pages to the configured run function, handling either a single URL or multiple URLs.

        Args:
            url: The URL of the first web page to load.
            *urls: Additional URLs of web pages to load, if any.

        Returns:
            A WebPage object if a single URL is provided, or a list of WebPage objects if multiple URLs are provided.
        """
        return await self.run_func(url, *urls)
