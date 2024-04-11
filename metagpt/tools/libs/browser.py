from playwright.async_api import async_playwright

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.logs import ToolLogItem, log_tool_output_async
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import encode_image


@register_tool()
class Browser:
    """
    A tool for browsing the web. Don't initialize a new instance of this class if one already exists.
    Note: Combine searching, scrolling, extraction, and link finding together to achieve most effective browsing. DON'T stick to one method.
    """

    def __init__(self):
        """initiate the browser, create pages placeholder later to be managed as {page_url: page object}"""
        self.browser = None

        from metagpt.config2 import config
        from metagpt.llm import LLM

        self.llm = LLM(llm_config=config.get_openai_llm())
        self.llm.model = "gpt-4-vision-preview"

        # browser status management
        self.pages = {}
        self.current_page_url = None
        self.current_page = None

    async def start(self):
        """Starts Playwright and launches a browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()

    def _set_current_page(self, page, url):
        self.current_page = page
        self.current_page_url = url
        print("Now on page ", url)

    async def open_new_page(self, url: str):
        """open a new page in the browser, set it as the current page"""
        page = await self.browser.new_page()
        await page.goto(url)
        self.pages[url] = page
        self._set_current_page(page, url)
        await log_tool_output_async(
            ToolLogItem(type="object", name="open_new_page", value=self.current_page), tool_name="Browser"
        )

    async def switch_page(self, url: str):
        """switch to an opened page in the browser, set it as the current page"""
        if url in self.pages:
            self._set_current_page(self.pages[url], url)
            await log_tool_output_async(
                ToolLogItem(type="object", name="switch_page", value=self.current_page), tool_name="Browser"
            )
        else:
            print(f"Page not found: {url}")

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
                content = await element.evaluate(
                    """
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
                )

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
        print(f"Successfully scrolled to the {index}-th search result, consider extract more info around it.")
        await log_tool_output_async(
            ToolLogItem(type="object", name="scroll_page", value=self.current_page), tool_name="Browser"
        )

    async def find_links(self) -> list:
        """Finds all links in the current page and returns a list of dictionaries with link text and the URL.
        Useful for navigating to more pages and exploring more resources.

        Returns:
            list: A list of dictionaries, each containing 'text' and 'href' keys.
        """
        # Use a CSS selector to find all <a> elements in the page.
        links = await self.current_page.query_selector_all("a")

        # Prepare an empty list to hold link information.
        link_info = []

        # Iterate over each link element to extract its text and href attributes.
        for link in links:
            text = await link.text_content()
            href = await link.get_attribute("href")
            link_info.append({"text": text, "href": href})

        print(f"Found {len(link_info)} links:\n\n{link_info}")

        return link_info

    async def extract_info_from_view(self, instruction: str) -> str:
        """
        Extract useful info from the current page view.

        Args:
            instruction (str): explain what info needs to be extracted

        Returns:
            str: extracted info from current view
        """
        img_path = DEFAULT_WORKSPACE_ROOT / "screenshot_temp.png"
        await self.current_page.screenshot(path=img_path)
        rsp = await self.llm.aask(msg=instruction, images=[encode_image(img_path)])
        return rsp

    async def scroll_current_page(self, offset: int = 500):
        """scroll the current page by offset pixels, negative value means scrolling up, returning the content observed after scrolling"""
        await self.current_page.evaluate(f"window.scrollBy(0, {offset})")
        print(f"Scrolled current page by {offset} pixels. Perceive the scrolled view if needed")
        await log_tool_output_async(
            ToolLogItem(type="object", name="scroll_page", value=self.current_page), tool_name="Browser"
        )

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
