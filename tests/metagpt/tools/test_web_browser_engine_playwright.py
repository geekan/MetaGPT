"""
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation.
"""

import pytest

from metagpt.config import CONFIG
from metagpt.tools import web_browser_engine_playwright
from metagpt.utils.parse_html import WebPage


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "browser_type, use_proxy, kwagrs, url, urls",
    [
        ("chromium", {"proxy": True}, {}, "https://deepwisdom.ai", ("https://deepwisdom.ai",)),
        ("firefox", {}, {"ignore_https_errors": True}, "https://deepwisdom.ai", ("https://deepwisdom.ai",)),
        ("webkit", {}, {"ignore_https_errors": True}, "https://deepwisdom.ai", ("https://deepwisdom.ai",)),
    ],
    ids=["chromium-normal", "firefox-normal", "webkit-normal"],
)
async def test_scrape_web_page(browser_type, use_proxy, kwagrs, url, urls, proxy, capfd):
    global_proxy = CONFIG.global_proxy
    try:
        if use_proxy:
            CONFIG.global_proxy = proxy
        browser = web_browser_engine_playwright.PlaywrightWrapper(browser_type=browser_type, **kwagrs)
        result = await browser.run(url)
        assert isinstance(result, WebPage)
        assert "MetaGPT" in result.inner_text

        if urls:
            results = await browser.run(url, *urls)
            assert isinstance(results, list)
            assert len(results) == len(urls) + 1
            assert all(("MetaGPT" in i.inner_text) for i in results)
        if use_proxy:
            assert "Proxy:" in capfd.readouterr().out
    finally:
        CONFIG.global_proxy = global_proxy


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
