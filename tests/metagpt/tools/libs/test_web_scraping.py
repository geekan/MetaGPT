import pytest

from metagpt.tools.libs.web_scraping import scrape_web_playwright


@pytest.mark.asyncio
async def test_scrape_web_playwright(http_server):
    server, test_url = await http_server()

    result = await scrape_web_playwright(test_url)

    # Assert that the result is a dictionary
    assert isinstance(result, dict)

    # Assert that the result contains 'inner_text' and 'html' keys
    assert "inner_text" in result
    assert "html" in result

    # Assert startswith and endswith
    assert not result["inner_text"].startswith(" ")
    assert not result["inner_text"].endswith(" ")
    assert not result["html"].startswith(" ")
    assert not result["html"].endswith(" ")
    await server.stop()
