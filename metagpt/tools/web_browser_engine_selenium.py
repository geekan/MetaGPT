#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import importlib
from concurrent import futures
from copy import deepcopy
from typing import Callable, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.core.download_manager import WDMDownloadManager
from webdriver_manager.core.http import WDMHttpClient

from metagpt.utils.parse_html import WebPage


class SeleniumWrapper(BaseModel):
    """Wrapper around Selenium.

    To use this module, you should check the following:

    1. Run the following command: pip install metagpt[selenium].
    2. Make sure you have a compatible web browser installed and the appropriate WebDriver set up
       for that browser before running. For example, if you have Mozilla Firefox installed on your
       computer, you can set the configuration SELENIUM_BROWSER_TYPE to firefox. After that, you
       can scrape web pages using the Selenium WebBrowserEngine.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    browser_type: Literal["chrome", "firefox", "edge", "ie"] = "chrome"
    launch_kwargs: dict = Field(default_factory=dict)
    proxy: Optional[str] = None
    loop: Optional[asyncio.AbstractEventLoop] = None
    executor: Optional[futures.Executor] = None
    _has_run_precheck: bool = PrivateAttr(False)
    _get_driver: Optional[Callable] = PrivateAttr(None)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if self.proxy and "proxy-server" not in self.launch_kwargs:
            self.launch_kwargs["proxy-server"] = self.proxy

    @property
    def launch_args(self):
        return [f"--{k}={v}" for k, v in self.launch_kwargs.items() if k != "executable_path"]

    @property
    def executable_path(self):
        return self.launch_kwargs.get("executable_path")

    async def run(self, url: str, *urls: str) -> WebPage | list[WebPage]:
        await self._run_precheck()

        _scrape = lambda url: self.loop.run_in_executor(self.executor, self._scrape_website, url)

        if urls:
            return await asyncio.gather(_scrape(url), *(_scrape(i) for i in urls))
        return await _scrape(url)

    async def _run_precheck(self):
        if self._has_run_precheck:
            return
        self.loop = self.loop or asyncio.get_event_loop()
        self._get_driver = await self.loop.run_in_executor(
            self.executor,
            lambda: _gen_get_driver_func(
                self.browser_type, *self.launch_args, executable_path=self.executable_path, proxy=self.proxy
            ),
        )
        self._has_run_precheck = True

    def _scrape_website(self, url):
        with self._get_driver() as driver:
            try:
                driver.get(url)
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                inner_text = driver.execute_script("return document.body.innerText;")
                html = driver.page_source
            except Exception as e:
                inner_text = f"Fail to load page content for {e}"
                html = ""
            return WebPage(inner_text=inner_text, html=html, url=url)


_webdriver_manager_types = {
    "chrome": ("webdriver_manager.chrome", "ChromeDriverManager"),
    "firefox": ("webdriver_manager.firefox", "GeckoDriverManager"),
    "edge": ("webdriver_manager.microsoft", "EdgeChromiumDriverManager"),
    "ie": ("webdriver_manager.microsoft", "IEDriverManager"),
}


class WDMHttpProxyClient(WDMHttpClient):
    def __init__(self, proxy: str = None):
        super().__init__()
        self.proxy = proxy

    def get(self, url, **kwargs):
        if "proxies" not in kwargs and self.proxy:
            kwargs["proxies"] = {"all": self.proxy}
        return super().get(url, **kwargs)


def _gen_get_driver_func(browser_type, *args, executable_path=None, proxy=None):
    WebDriver = getattr(importlib.import_module(f"selenium.webdriver.{browser_type}.webdriver"), "WebDriver")
    Service = getattr(importlib.import_module(f"selenium.webdriver.{browser_type}.service"), "Service")
    Options = getattr(importlib.import_module(f"selenium.webdriver.{browser_type}.options"), "Options")

    if not executable_path:
        module_name, type_name = _webdriver_manager_types[browser_type]
        DriverManager = getattr(importlib.import_module(module_name), type_name)
        driver_manager = DriverManager(download_manager=WDMDownloadManager(http_client=WDMHttpProxyClient(proxy=proxy)))
        # driver_manager.driver_cache.find_driver(driver_manager.driver))
        executable_path = driver_manager.install()

    def _get_driver():
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--enable-javascript")
        if browser_type == "chrome":
            options.add_argument("--disable-gpu")  # This flag can help avoid renderer issue
            options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
            options.add_argument("--no-sandbox")
        for i in args:
            options.add_argument(i)
        return WebDriver(options=deepcopy(options), service=Service(executable_path=executable_path))

    return _get_driver
