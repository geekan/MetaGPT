from metagpt.tools.tool_registry import register_tool
from metagpt.tools.web_browser_engine_playwright import PlaywrightWrapper


@register_tool(tags=["web scraping", "web"])
async def scrape_web_playwright(url):
    """
    Asynchronously Scrape and save the HTML structure and inner text content of a web page using Playwright.

    Args:
        url (str): The main URL to fetch inner text from.

    Returns:
        dict: The inner text content and html structure of the web page, keys are 'inner_text', 'html'.
    """
    # Create a PlaywrightWrapper instance for the Chromium browser
    web = await PlaywrightWrapper().run(url)

    # Return the inner text content of the web page
    return {"inner_text": web.inner_text.strip(), "html": web.html.strip()}
