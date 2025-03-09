from __future__ import annotations

import time
from typing import Literal, Optional

from playwright.async_api import Browser as Browser_
from playwright.async_api import (
    BrowserContext,
    Frame,
    Page,
    Playwright,
    Request,
    async_playwright,
)
from pydantic import BaseModel, ConfigDict, Field

from metagpt.tools.tool_registry import register_tool
from metagpt.utils.a11y_tree import (
    click_element,
    get_accessibility_tree,
    get_backend_node_id,
    hover_element,
    key_press,
    parse_accessibility_tree,
    scroll_page,
    type_text,
)
from metagpt.utils.proxy_env import get_proxy_from_env
from metagpt.utils.report import BrowserReporter


@register_tool(
    tags=["web", "browse"],
    include_functions=[
        "click",
        "close_tab",
        "go_back",
        "go_forward",
        "goto",
        "hover",
        "press",
        "scroll",
        "tab_focus",
        "type",
    ],
)
class Browser(BaseModel):
    """A tool for browsing the web. Don't initialize a new instance of this class if one already exists.

    Note: If you plan to use the browser to assist you in completing tasks, then using the browser should be a standalone
    task, executing actions each time based on the content seen on the webpage before proceeding to the next step.

    ## Example
    Issue: The details of the latest issue in the geekan/MetaGPT repository.
    Plan: Use a browser to view the details of the latest issue in the geekan/MetaGPT repository.
    Solution:
    Let's first open the issue page of the MetaGPT repository with the `Browser.goto` command

    >>> await browser.goto("https://github.com/geekan/MetaGPT/issues")

    From the output webpage, we've identified that the latest issue can be accessed by clicking on the element with ID "1141".

    >>> await browser.click(1141)

    Finally, we have found the webpage for the latest issue, we can close the tab and finish current task.

    >>> await browser.close_tab()
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    playwright: Optional[Playwright] = Field(default=None, exclude=True)
    browser_instance: Optional[Browser_] = Field(default=None, exclude=True)
    browser_ctx: Optional[BrowserContext] = Field(default=None, exclude=True)
    page: Optional[Page] = Field(default=None, exclude=True)
    accessibility_tree: list = Field(default_factory=list)
    headless: bool = Field(default=True)
    proxy: Optional[dict] = Field(default_factory=get_proxy_from_env)
    is_empty_page: bool = Field(default=True)
    reporter: BrowserReporter = Field(default_factory=BrowserReporter)

    async def start(self) -> None:
        """Starts Playwright and launches a browser"""
        if self.playwright is None:
            self.playwright = playwright = await async_playwright().start()
            browser = self.browser_instance = await playwright.chromium.launch(headless=self.headless, proxy=self.proxy)
            browser_ctx = self.browser_ctx = await browser.new_context()
            self.page = await browser_ctx.new_page()

    async def stop(self):
        if self.playwright:
            playwright = self.playwright
            self.playwright = None
            self.browser_instance = None
            self.browser_ctx = None
            await playwright.stop()

    async def click(self, element_id: int):
        """clicks on an element with a specific id on the webpage."""
        await click_element(self.page, get_backend_node_id(element_id, self.accessibility_tree))
        return await self._wait_page()

    async def type(self, element_id: int, content: str, press_enter_after: bool = False):
        """Use this to type the content into the field with id."""
        if press_enter_after:
            content += "\n"
        await click_element(self.page, get_backend_node_id(element_id, self.accessibility_tree))
        await type_text(self.page, content)
        return await self._wait_page()

    async def hover(self, element_id: int):
        """Hover over an element with id."""
        await hover_element(self.page, get_backend_node_id(element_id, self.accessibility_tree))
        return await self._wait_page()

    async def press(self, key_comb: str):
        """Simulates the pressing of a key combination on the keyboard (e.g., Ctrl+v)."""
        await key_press(self.page, key_comb)
        return await self._wait_page()

    async def scroll(self, direction: Literal["down", "up"]):
        """Scroll the page up or down."""
        await scroll_page(self.page, direction)
        return await self._wait_page()

    async def goto(self, url: str, timeout: float = 90000):
        """Navigate to a specific URL."""
        if self.page is None:
            await self.start()
        async with self.reporter as reporter:
            await reporter.async_report(url, "url")
            await self.page.goto(url, timeout=timeout)
            self.is_empty_page = False
            return await self._wait_page()

    async def go_back(self):
        """Navigate to the previously viewed page."""
        await self.page.go_back()
        return await self._wait_page()

    async def go_forward(self):
        """Navigate to the next page (if a previous 'go_back' action was performed)."""
        await self.page.go_forward()
        return await self._wait_page()

    async def tab_focus(self, page_number: int):
        """Open a new, empty browser tab."""
        page = self.browser_ctx.pages[page_number]
        await page.bring_to_front()
        return await self._wait_page()

    async def close_tab(self):
        """Close the currently active tab."""
        await self.page.close()
        if len(self.browser_ctx.pages) > 0:
            self.page = self.browser_ctx.pages[-1]
        else:
            self.page = await self.browser_ctx.new_page()
            self.is_empty_page = True
        return await self._wait_page()

    async def _wait_page(self):
        page = self.page
        await self._wait_until_page_idle(page)
        self.accessibility_tree = await get_accessibility_tree(page)
        await self.reporter.async_report(page, "page")
        return f"SUCCESS, URL: {page.url} have been loaded."

    def _register_page_event(self, page: Page):
        page.last_busy_time = time.time()
        page.requests = set()
        page.on("domcontentloaded", self._update_page_last_busy_time)
        page.on("load", self._update_page_last_busy_time)
        page.on("request", self._on_page_request)
        page.on("requestfailed", self._on_page_requestfinished)
        page.on("requestfinished", self._on_page_requestfinished)
        page.on("frameattached", self._on_frame_change)
        page.on("framenavigated", self._on_frame_change)

    async def _wait_until_page_idle(self, page) -> None:
        if not hasattr(page, "last_busy_time"):
            self._register_page_event(page)
        else:
            page.last_busy_time = time.time()
        while time.time() - page.last_busy_time < 0.5:
            await page.wait_for_timeout(100)

    async def _update_page_last_busy_time(self, page: Page):
        page.last_busy_time = time.time()

    async def _on_page_request(self, request: Request):
        page = request.frame.page
        page.requests.add(request)
        await self._update_page_last_busy_time(page)

    async def _on_page_requestfinished(self, request: Request):
        request.frame.page.requests.discard(request)

    async def _on_frame_change(self, frame: Frame):
        await self._update_page_last_busy_time(frame.page)

    async def view(self):
        observation = parse_accessibility_tree(self.accessibility_tree)
        return f"Current Browser Viewer\n URL: {self.page.url}\nOBSERVATION:\n{observation[0]}\n"

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.stop()
