"""
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation.
"""

import pytest

from metagpt.config import Config
from metagpt.tools import WebBrowserEngineType, web_browser_engine


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
    conf = Config()
    browser = web_browser_engine.WebBrowserEngine(options=conf.runtime_options, engine=browser_type)
    result = await browser.run(url)
    assert isinstance(result, str)
    assert "深度赋智" in result

    if urls:
        results = await browser.run(url, *urls)
        assert isinstance(results, list)
        assert len(results) == len(urls) + 1
        assert all(("深度赋智" in i) for i in results)
