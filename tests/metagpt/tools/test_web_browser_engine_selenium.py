import pytest

from metagpt.config import CONFIG
from metagpt.tools import web_browser_engine_selenium


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "browser_type, use_proxy, url, urls",
    [
        ("chrome", True, "https://fuzhi.ai", ("https://fuzhi.ai",)),
        ("firefox", False, "https://fuzhi.ai", ("https://fuzhi.ai",)),
        ("edge", False, "https://fuzhi.ai", ("https://fuzhi.ai",)),
    ],
    ids=["chrome-normal", "firefox-normal", "edge-normal"],
)
async def test_scrape_web_page(browser_type, use_proxy, url, urls, proxy, capfd):
    try:
        global_proxy = CONFIG.global_proxy
        if use_proxy:
            CONFIG.global_proxy = proxy
        browser = web_browser_engine_selenium.SeleniumWrapper(browser_type)
        result = await browser.run(url)
        result = result.inner_text
        assert isinstance(result, str)
        assert "Deepwisdom" in result

        if urls:
            results = await browser.run(url, *urls)
            assert isinstance(results, list)
            assert len(results) == len(urls) + 1
            assert all(("Deepwisdom" in i.inner_text) for i in results)
        if use_proxy:
            assert "Proxy:" in capfd.readouterr().out
    finally:
        CONFIG.global_proxy = global_proxy
