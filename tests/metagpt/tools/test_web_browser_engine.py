#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from metagpt.tools import WebBrowserEngineType, web_browser_engine
from metagpt.utils.parse_html import WebPage


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "browser_type, url, urls",
    [
        (WebBrowserEngineType.PLAYWRIGHT, "https://deepwisdom.ai", ("https://deepwisdom.ai",)),
        (WebBrowserEngineType.SELENIUM, "https://deepwisdom.ai", ("https://deepwisdom.ai",)),
    ],
    ids=["playwright", "selenium"],
)
async def test_scrape_web_page(browser_type, url, urls):
    browser = web_browser_engine.WebBrowserEngine(engine=browser_type)
    result = await browser.run(url)
    assert isinstance(result, WebPage)
    assert "MetaGPT" in result.inner_text

    if urls:
        results = await browser.run(url, *urls)
        assert isinstance(results, list)
        assert len(results) == len(urls) + 1
        assert all(("MetaGPT" in i.inner_text) for i in results)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
