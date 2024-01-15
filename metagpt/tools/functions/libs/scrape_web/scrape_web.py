import asyncio

from metagpt.tools.web_browser_engine_playwright import PlaywrightWrapper


async def scrape_web(url, *urls):
    """
    Scrape and save the HTML structure and inner text content of a web page using Playwright.

    Args:
        url (str): The main URL to fetch inner text from.
        *urls (str): Additional URLs to fetch inner text from.

    Returns:
        (dict): The inner text content and html structure of the web page, key are : 'inner_text', 'html'.

    Raises:
        Any exceptions that may occur during the Playwright operation.
    """
    # Create a PlaywrightWrapper instance for the Chromium browser
    web = await PlaywrightWrapper("chromium").run(url, *urls)

    # Return the inner text content of the web page
    return {"inner_text": web.inner_text, "html": web.html}

# 需要改三个地方: yaml, 对应路径下init, MetaGPT/metagpt/prompts/ml_engineer.py中ML_MODULE_MAP
