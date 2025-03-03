import pytest

from metagpt.tools.libs.web_scraping import view_page_element_to_scrape


@pytest.mark.asyncio
async def test_view_page_element_to_scrape():
    # Define the test URL and parameters
    test_url = "https://docs.deepwisdom.ai/main/zh/"
    test_requirement = "Retrieve all paragraph texts"
    test_keep_links = True
    test_page = await view_page_element_to_scrape(test_url, test_requirement, test_keep_links)
    assert isinstance(test_page, str)
    assert "html" in test_page
