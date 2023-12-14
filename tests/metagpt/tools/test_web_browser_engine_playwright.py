"""
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation.
"""

import pytest

from metagpt.config import Config
from metagpt.tools import web_browser_engine_playwright


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
    conf = Config()
    global_proxy = conf.global_proxy
    try:
        if use_proxy:
            conf.global_proxy = proxy
        browser = web_browser_engine_playwright.PlaywrightWrapper(
            options=conf.runtime_options, browser_type=browser_type, **kwagrs
        )
        result = await browser.run(url)
        result = result.inner_text
        assert isinstance(result, str)
        assert "DeepWisdom" in result

        if urls:
            results = await browser.run(url, *urls)
            assert isinstance(results, list)
            assert len(results) == len(urls) + 1
            assert all(("DeepWisdom" in i) for i in results)
        if use_proxy:
            assert "Proxy:" in capfd.readouterr().out
    finally:
        conf.global_proxy = global_proxy
