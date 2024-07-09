import contextlib
from uuid import uuid4

from metagpt.tools.libs.browser import Browser
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.file import MemoryFileSystem
from metagpt.utils.parse_html import simplify_html


@register_tool(tags=["web scraping"])
async def view_page_element_to_scrape(url: str, requirement: str, keep_links: bool = False) -> str:
    """view the HTML content of current page to understand the structure.

    Args:
        url (str): The URL of the web page to scrape.
        requirement (str): Providing a clear and detailed requirement helps in focusing the inspection on the desired elements.
        keep_links (bool): Whether to keep the hyperlinks in the HTML content. Set to True if links are required
    Returns:
        str: The HTML content of the page.
    """
    async with Browser() as browser:
        await browser.goto(url)
        page = browser.page
        html = await page.content()
        html = simplify_html(html, url=page.url, keep_links=keep_links)
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
    return html


# async def get_elements_outerhtml(self, element_ids: list[int]):
#     """Inspect the outer HTML of the elements in Current Browser Viewer.
#     """
#     page = self.page
#     data = []
#     for element_id in element_ids:
#         html = await get_element_outer_html(page, get_backend_node_id(element_id, self.accessibility_tree))
#         data.append(html)
#     return "\n".join(f"[{element_id}]. {html}" for element_id, html in zip(element_ids, data))
