from metagpt.tools.tool_registry import register_tool
from metagpt.tools.tool_type import ToolType
from metagpt.tools.web_browser_engine_playwright import PlaywrightWrapper


@register_tool(tool_type=ToolType.WEBSCRAPING.type_name)
async def scrape_web_playwright(url, *urls):
    """
    Scrape and save the HTML structure and inner text content of a web page using Playwright.

    Args:
        url (str): The main URL to fetch inner text from.
        *urls (str): Additional URLs to fetch inner text from.

    Returns:
        (dict): The inner text content and html structure of the web page, key are : 'inner_text', 'html'.
    """
    # Create a PlaywrightWrapper instance for the Chromium browser
    web = await PlaywrightWrapper().run(url, *urls)

    # Return the inner text content of the web page
    return {"inner_text": web.inner_text.strip(), "html": web.html.strip()}
