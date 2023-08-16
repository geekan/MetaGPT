import pytest

from metagpt.config import CONFIG
from metagpt.tools import web_browser_engine_playwright


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "browser_type, use_proxy, kwagrs, url, urls",
    [
        ("chromium", {"proxy": True}, {}, "https://fuzhi.ai", ("https://fuzhi.ai",)),
        ("firefox", {}, {"ignore_https_errors": True}, "https://fuzhi.ai", ("https://fuzhi.ai",)),
        ("webkit", {}, {"ignore_https_errors": True}, "https://fuzhi.ai", ("https://fuzhi.ai",)),
    ],
    ids=["chromium-normal", "firefox-normal", "webkit-normal"],
)
async def test_scrape_web_page(browser_type, use_proxy, kwagrs, url, urls, proxy, capfd):
    try:
        global_proxy = CONFIG.global_proxy
        if use_proxy:
            CONFIG.global_proxy = proxy
        browser = web_browser_engine_playwright.PlaywrightWrapper(browser_type, **kwagrs)
        result = await browser.run(url)
        result = result.inner_text
        assert isinstance(result, str)
        assert "Deepwisdom" in result

        if urls:
            results = await browser.run(url, *urls)
            assert isinstance(results, list)
            assert len(results) == len(urls) + 1
            assert all(("Deepwisdom" in i) for i in results)
        if use_proxy:
            assert "Proxy:" in capfd.readouterr().out
    finally:
        CONFIG.global_proxy = global_proxy
