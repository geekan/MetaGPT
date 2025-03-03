from __future__ import annotations

from typing import Optional

from playwright.async_api import Browser as Browser_
from playwright.async_api import BrowserContext, Page, Playwright, async_playwright
from pydantic import BaseModel, ConfigDict, Field

from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import decode_image
from metagpt.utils.proxy_env import get_proxy_from_env
from metagpt.utils.report import BrowserReporter

DOWNLOAD_PICTURE_JAVASCRIPT = """
async () => {{
    var img = document.querySelector('{img_element_selector}');
    if (img && img.src) {{
        const response = await fetch(img.src);
        if (response.ok) {{
            const blob = await response.blob();
            return await new Promise(resolve => {{
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.readAsDataURL(blob);
            }});
        }}
    }}
    return null;
}}
"""


@register_tool(include_functions=["get_image"])
class ImageGetter(BaseModel):
    """
    A tool to get images.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    playwright: Optional[Playwright] = Field(default=None, exclude=True)
    browser_instance: Optional[Browser_] = Field(default=None, exclude=True)
    browser_ctx: Optional[BrowserContext] = Field(default=None, exclude=True)
    page: Optional[Page] = Field(default=None, exclude=True)
    headless: bool = Field(default=True)
    proxy: Optional[dict] = Field(default_factory=get_proxy_from_env)
    reporter: BrowserReporter = Field(default_factory=BrowserReporter)
    url: str = "https://unsplash.com/s/photos/{search_term}/"
    img_element_selector: str = ".zNNw1 > div > img:nth-of-type(2)"

    async def start(self) -> None:
        """Starts Playwright and launches a browser"""
        if self.playwright is None:
            self.playwright = playwright = await async_playwright().start()
            browser = self.browser_instance = await playwright.chromium.launch(headless=self.headless, proxy=self.proxy)
            browser_ctx = self.browser_ctx = await browser.new_context()
            self.page = await browser_ctx.new_page()

    async def get_image(self, search_term, image_save_path):
        """
        Get an image related to the search term.

        Args:
            search_term (str): The term to search for the image. The search term must be in English. Using any other language may lead to a mismatch.
            image_save_path (str): The file path where the image will be saved.
        """
        # Search for images from https://unsplash.com/s/photos/

        if self.page is None:
            await self.start()
        await self.page.goto(self.url.format(search_term=search_term), wait_until="domcontentloaded")
        # Wait until the image element is loaded
        try:
            await self.page.wait_for_selector(self.img_element_selector)
        except TimeoutError:
            return f"{search_term} not found. Please broaden the search term."
        # Get the base64 code of the first  retrieved image
        image_base64 = await self.page.evaluate(
            DOWNLOAD_PICTURE_JAVASCRIPT.format(img_element_selector=self.img_element_selector)
        )
        if image_base64:
            image = decode_image(image_base64)
            image.save(image_save_path)
            return f"{search_term} found. The image is saved in {image_save_path}."
        return f"{search_term} not found. Please broaden the search term."
