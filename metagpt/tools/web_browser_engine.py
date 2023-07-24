#!/usr/bin/env python

from __future__ import annotations
import asyncio
import importlib

from typing import Any, Callable, Coroutine, overload

from metagpt.config import CONFIG
from metagpt.tools import WebBrowserEngineType
from bs4 import BeautifulSoup


class WebBrowserEngine:
    def __init__(
        self,
        engine: WebBrowserEngineType | None = None,
        run_func: Callable[..., Coroutine[Any, Any, str | list[str]]] | None = None,
        parse_func: Callable[[str], str] | None = None,
    ):
        engine = engine or CONFIG.web_browser_engine

        if engine == WebBrowserEngineType.PLAYWRIGHT:
            web_browser_engine = importlib.import_module("metagpt.tools.web_browser_engine_playwright")
            run_func = web_browser_engine.PlaywrightWrapper().run
        elif engine == WebBrowserEngineType.SELENIUM:
            web_browser_engine = importlib.import_module("metagpt.tools.web_browser_engine_selenium")
            run_func = web_browser_engine.SeleniumWrapper().run
        elif engine == WebBrowserEngineType.CUSTOM:
            run_func = run_func
        else:
            raise NotImplementedError
        self.parse_func = parse_func or get_page_content
        self.run_func = run_func
        self.engine = engine

    @overload
    async def run(self, url: str) -> str:
        ...

    @overload
    async def run(self, url: str, *urls: str) -> list[str]:
        ...

    async def run(self, url: str, *urls: str) -> str | list[str]:
        page = await self.run_func(url, *urls)
        if isinstance(page, str):
            return self.parse_func(page)
        return [self.parse_func(i) for i in page]


def get_page_content(page: str):
    soup = BeautifulSoup(page, "html.parser")
    return "\n".join(i.text.strip() for i in soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "pre"]))


if __name__ == "__main__":
    text = asyncio.run(WebBrowserEngine().run("https://fuzhi.ai/"))
    print(text)
