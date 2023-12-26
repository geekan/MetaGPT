"""
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation.
"""

import pytest

from metagpt.config import CONFIG
from metagpt.tools import web_browser_engine_selenium
from metagpt.utils.parse_html import WebPage


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "browser_type, use_proxy, url, urls",
    [
        ("chrome", True, "https://deepwisdom.ai", ("https://deepwisdom.ai",)),
        ("firefox", False, "https://deepwisdom.ai", ("https://deepwisdom.ai",)),
        ("edge", False, "https://deepwisdom.ai", ("https://deepwisdom.ai",)),
    ],
    ids=["chrome-normal", "firefox-normal", "edge-normal"],
)
async def test_scrape_web_page(browser_type, use_proxy, url, urls, proxy, capfd):
    # Prerequisites
    # firefox, chrome, Microsoft Edge

    global_proxy = CONFIG.global_proxy
    try:
        if use_proxy:
            CONFIG.global_proxy = proxy
        browser = web_browser_engine_selenium.SeleniumWrapper(browser_type=browser_type)
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
