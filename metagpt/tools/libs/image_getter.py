from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from typing import Optional

from playwright.async_api import Browser as Browser_
from playwright.async_api import BrowserContext, Page, Playwright, async_playwright
from pydantic import BaseModel, ConfigDict, Field

from metagpt.tools.tool_registry import register_tool
from metagpt.utils.proxy_env import get_proxy_from_env
from metagpt.utils.report import BrowserReporter


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

    async def start(self) -> None:
        """Starts Playwright and launches a browser"""
        if self.playwright is None:
            self.playwright = playwright = await async_playwright().start()
            browser = self.browser_instance = await playwright.chromium.launch(headless=self.headless, proxy=self.proxy)
            browser_ctx = self.browser_ctx = await browser.new_context()
            self.page = await browser_ctx.new_page()

    async def get_image(self, search_term, save_file_path):
        """
        Get an image related to the search term.

        Args:
            search_term (str): The term to search for the image.
            save_file_path (str): The file path where the image will
        """
        # Seach image
        url = f"https://unsplash.com/s/photos/{search_term}/"
        if self.page is None:
            await self.start()
        await self.page.goto(url, wait_until="domcontentloaded")
        # Wait for the element
        try:
            await self.page.wait_for_selector(".zNNw1 > div > img:nth-of-type(2)")
        except TimeoutError:
            return f"{search_term} not found. Please broaden the search term."

        image_base64 = await self.page.evaluate(
            """async () => {
            var img = document.querySelector('.zNNw1 > div > img:nth-of-type(2)');
            if (img && img.src) {
                const response = await fetch(img.src);
                if (response.ok) {
                    const blob = await response.blob();
                    return await new Promise(resolve => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    });
                }
            }
            return null;
        }"""
        )
        if image_base64:
            file_path = Path(save_file_path)
            os.makedirs(file_path.parent, exist_ok=True)
            with open(save_file_path, "wb") as f:
                imgstr = re.sub("data:image/.*?;base64,", "", image_base64)
                image_data = base64.b64decode(imgstr)
                f.write(image_data)
            return f"{search_term} found. The image is saved in {save_file_path}."
        else:
            return f"{search_term} not found. Please broaden the search term."
