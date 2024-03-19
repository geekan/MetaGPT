#!/usr/bin/env python
# -*- coding: utf-8 -*-

import browsers
import pytest

from metagpt.tools import web_browser_engine_selenium
from metagpt.utils.parse_html import WebPage


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "browser_type, use_proxy, url, urls",
    [
        pytest.param(
            "chrome",
            True,
            "https://deepwisdom.ai",
            ("https://deepwisdom.ai",),
            marks=pytest.mark.skipif(not browsers.get("chrome"), reason="chrome browser not found"),
        ),
        pytest.param(
            "firefox",
            False,
            "https://deepwisdom.ai",
            ("https://deepwisdom.ai",),
            marks=pytest.mark.skipif(not browsers.get("firefox"), reason="firefox browser not found"),
        ),
        pytest.param(
            "edge",
            False,
            "https://deepwisdom.ai",
            ("https://deepwisdom.ai",),
            marks=pytest.mark.skipif(not browsers.get("msedge"), reason="edge browser not found"),
        ),
    ],
    ids=["chrome-normal", "firefox-normal", "edge-normal"],
)
async def test_scrape_web_page(browser_type, use_proxy, url, urls, proxy, capfd):
    # Prerequisites
    # firefox, chrome, Microsoft Edge
    proxy_url = None
    if use_proxy:
        server, proxy_url = await proxy()
    browser = web_browser_engine_selenium.SeleniumWrapper(browser_type=browser_type, proxy=proxy_url)
    result = await browser.run(url)
    assert isinstance(result, WebPage)
    assert "MetaGPT" in result.inner_text

    if urls:
        results = await browser.run(url, *urls)
        assert isinstance(results, list)
        assert len(results) == len(urls) + 1
        assert all(("MetaGPT" in i.inner_text) for i in results)
    if use_proxy:
        server.close()
        assert "Proxy:" in capfd.readouterr().out


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
