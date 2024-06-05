from __future__ import annotations

import contextlib
from uuid import uuid4

from playwright.async_api import async_playwright

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.file import MemoryFileSystem
from metagpt.utils.parse_html import simplify_html
from metagpt.utils.report import BrowserReporter


@register_tool(tags=["web", "browse", "scrape"])
class Browser:
    """
    A tool for browsing the web and scraping. Don't initialize a new instance of this class if one already exists.
    Note: Combine searching and scrolling together to achieve most effective browsing. DON'T stick to one method.
    """

    def __init__(self):
        """initiate the browser, create pages placeholder later to be managed as {page_url: page object}"""
        self.browser = None

        # browser status management
        self.pages = {}
        self.current_page_url = None
        self.current_page = None
        self.reporter = BrowserReporter()

    async def start(self):
        """Starts Playwright and launches a browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()

    async def _set_current_page(self, page, url):
        self.current_page = page
        self.current_page_url = url
        print("Now on page ", url)
        await self._view()

    async def open_new_page(self, url: str, timeout: float = 30000):
        """open a new page in the browser and view the page"""
        async with self.reporter as reporter:
            page = await self.browser.new_page()
            await reporter.async_report(url, "url")
            await page.goto(url, timeout=timeout)
            self.pages[url] = page
            await self._set_current_page(page, url)
            await reporter.async_report(page, "page")

    async def view_page_element_to_scrape(self, requirement: str, keep_links: bool = False) -> None:
        """view the HTML content of current page to understand the structure. When executed, the content will be printed out

        Args:
            requirement (str): Providing a clear and detailed requirement helps in focusing the inspection on the desired elements.
            keep_links (bool): Whether to keep the hyperlinks in the HTML content. Set to True if links are required
        """
        html = await self.current_page.content()
        html = simplify_html(html, url=self.current_page.url, keep_links=keep_links)
        mem_fs = MemoryFileSystem()
        filename = f"{uuid4().hex}.html"
        with mem_fs.open(filename, "w") as f:
            f.write(html)

        # Since RAG is an optional optimization, if it fails, the simplified HTML can be used as a fallback.
        with contextlib.suppress(Exception):
            from metagpt.rag.engines import SimpleEngine  # avoid circular import

            # TODO make `from_docs` asynchronous
            engine = SimpleEngine.from_docs(input_files=[filename], fs=mem_fs)
            nodes = await engine.aretrieve(requirement)
            html = "\n".join(i.text for i in nodes)

        mem_fs.rm_file(filename)
        print(html)

    async def get_page_content(self) -> str:
        """Get the HTML content of current page."""
        html = await self.current_page.content()
        html_content = html.strip()
        return html_content

    async def switch_page(self, url: str):
        """switch to an opened page in the browser and view the page"""
        if url in self.pages:
            await self._set_current_page(self.pages[url], url)
            await self.reporter.async_report(self.current_page, "page")
        else:
            print(f"Page not found: {url}")

    async def _view_page_html(self, keep_len: int = 5000) -> str:
        """view the HTML content of current page, return the HTML content as a string. When executed, the content will be printed out"""
        html = await self.current_page.content()
        html_content = html.strip()[:keep_len]
        return html_content

    async def search_content_all(self, search_term: str) -> list[dict]:
        """search all occurences of search term in the current page and return the search results with their position.
        Useful if you have a keyword or sentence in mind and want to quickly narrow down the content relevant to it.

        Args:
            search_term (str): the search term

        Returns:
            list[dict]: a list of dictionaries containing the elements and their positions, e.g.
            [
                {
                    "index": ...,
                    "content": {
                        "text_block": ...,
                        "links": [
                            {"text": ..., "href": ...},
                            ...
                        ]
                    },
                    "position": {from_top: ..., from_left: ...},
                },
                ...
            ]
        """
        locator = self.current_page.locator(f"text={search_term}")
        count = await locator.count()
        search_results = []
        for i in range(count):
            element = locator.nth(i)
            if await element.is_visible():
                position = await element.evaluate("e => ({ from_top: e.offsetTop, from_left: e.offsetLeft })")

                # Retrieve the surrounding block of text and links with their text
                content = await element.evaluate(SEARCH_CONTENT_JS)

                search_results.append(
                    {"index": len(search_results), "content": content, "position": position, "element_obj": element}
                )

        print(f"Found {len(search_results)} instances of the term '{search_term}':\n\n{search_results}")

        return search_results

    async def scroll_to_search_result(self, search_results: list[dict], index: int = 0):
        """Scroll to the index-th search result, potentially for subsequent perception.
        Useful if you have located a search result, the search result does not fulfill your requirement, and you need more information around that search result. Can only be used after search_all_content.

        Args:
            search_results (list[dict]): search_results from search_content_all
            index (int, optional): the index of the search result to scroll to. Index starts from 0. Defaults to 0.
        """
        if not search_results:
            return {}
        if index >= len(search_results):
            print(f"Index {index} is out of range. Scrolling to the last instance.")
            index = len(search_results) - 1
        element = search_results[index]["element_obj"]
        await element.scroll_into_view_if_needed()
        await self.reporter.async_report(self.current_page, "page")

        print(f"Successfully scrolled to the {index}-th search result")
        print(await self._view())

    # async def find_links(self) -> list:
    #     """Finds all links in the current page and returns a list of dictionaries with link text and the URL.
    #     Useful for navigating to more pages and exploring more resources.

    #     Returns:
    #         list: A list of dictionaries, each containing 'text' and 'href' keys.
    #     """
    #     # Use a CSS selector to find all <a> elements in the page.
    #     links = await self.current_page.query_selector_all("a")

    #     # Prepare an empty list to hold link information.
    #     link_info = []

    #     # Iterate over each link element to extract its text and href attributes.
    #     for link in links:
    #         text = await link.text_content()
    #         href = await link.get_attribute("href")
    #         link_info.append({"text": text, "href": href})

    #     print(f"Found {len(link_info)} links:\n\n{link_info}")

    #     return link_info

    async def screenshot(self, path: str = DEFAULT_WORKSPACE_ROOT / "screenshot_temp.png"):
        """Take a screenshot of the current page and save it to the specified path."""
        await self.current_page.screenshot(path=path)
        print(f"Screenshot saved to: {path}")

    async def _view(self, keep_len: int = 5000) -> str:
        """simulate human viewing the current page, return the visible text with links"""
        # visible_text_with_links = await self.current_page.evaluate(VIEW_CONTENT_JS)
        # print("The visible text and their links (if any): ", visible_text_with_links[:keep_len])
        # html_content = await self._view_page_html(keep_len=keep_len)
        # print("The html content: ", html_content)

    async def scroll_current_page(self, offset: int = 500):
        """scroll the current page by offset pixels, negative value means scrolling up, will print out observed content after scrolling"""
        await self.current_page.evaluate(f"window.scrollBy(0, {offset})")
        await self.reporter.async_report(self.current_page, "page")

        print(f"Scrolled current page by {offset} pixels.")
        print(await self._view())

    def check_all_pages(self) -> dict:
        """return all pages opened in the browser, a dictionary with {page_url: page_title}, useful for understanding the current browser state"""
        pages_info = {url: page.title() for url, page in self.pages.items()}
        return pages_info

    async def close(self):
        """close the browser and all pages"""
        await self.browser.close()
        await self.playwright.stop()


async def get_scroll_position(page):
    return await page.evaluate("() => ({ x: window.scrollX, y: window.scrollY })")


SEARCH_CONTENT_JS = """
(element) => {
    // const block = element.closest('p, div, section, article');
    const block = element.parentElement;
    return {
        text_block: block.innerText,
        // Create an array of objects, each containing the text and href of a link
        links: Array.from(block.querySelectorAll('a')).map(a => ({
            text: a.innerText, 
            href: a.href
        }))
    };
}
"""


VIEW_CONTENT_JS = """
() => {
    return Array.from(document.querySelectorAll('body *')).filter(el => {
        if (!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility !== 'visible' || style.opacity === '0') return false;
        const rect = el.getBoundingClientRect();
        const elemCenter = {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2
        };
        if (elemCenter.x < 0 || elemCenter.y < 0 || elemCenter.x > window.innerWidth || elemCenter.y > window.innerHeight) return false;
        if (document.elementFromPoint(elemCenter.x, elemCenter.y) !== el) return false;
        return true;
    }).map(el => {
        let text = el.innerText || '';
        text = text.trim();
        if (!text.length) return '';
        const parentAnchor = el.closest('a');
        if (parentAnchor && parentAnchor.href) {
            return `${text} (${parentAnchor.href})`;
        }
        return text;
    }).filter(text => text.length > 0).join("\\n");
}
"""
