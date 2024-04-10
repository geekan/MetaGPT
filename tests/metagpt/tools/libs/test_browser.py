import pytest

from metagpt.const import TEST_DATA_PATH
from metagpt.tools.libs.browser import Browser, get_scroll_position

TEST_URL = "https://docs.deepwisdom.ai/main/en/guide/get_started/quickstart.html"

TEST_SCREENSHOT_PATH = TEST_DATA_PATH / "screenshot.png"


@pytest.fixture(autouse=True)
def llm_mock(rsp_cache, mocker, request):
    # An empty fixture to overwrite the global llm_mock fixture
    # because in provider folder, we want to test the aask and aask functions for the specific models
    pass


@pytest.fixture
def browser():
    browser_instance = Browser()
    yield browser_instance


@pytest.mark.asyncio
async def test_open_and_switch_page(browser):
    await browser.start()

    await browser.open_new_page("https://baidu.com")
    await browser.open_new_page("https://tencent.com")
    assert browser.current_page_url == "https://tencent.com"
    await browser.switch_page("https://baidu.com")
    assert browser.current_page_url == "https://baidu.com"

    await browser.close()


@pytest.mark.asyncio
async def test_search(browser):
    await browser.start()

    # search all
    await browser.open_new_page(TEST_URL)
    search_term = "startup example"
    search_results = await browser.search_content_all(search_term)
    print(search_results)
    # expected search result as of 20240410:
    # [{'index': 0, 'content': {'text_block': 'Below is a breakdown of the software startup example. If you install MetaGPT with the git clone approach, simply run', 'links': [{'text': 'software startup example', 'href': 'https://github.com/geekan/MetaGPT/blob/main/metagpt/software_company.py'}]}, 'position': {'from_top': 640, 'from_left': 225}, 'element_obj': <Locator frame=<Frame name= url='https://docs.deepwisdom.ai/main/en/guide/get_started/quickstart.html'> selector='text=startup example >> nth=0'>}]
    first_result = search_results[0]["content"]
    assert "software startup example" in first_result["text_block"]
    assert first_result["links"]
    assert first_result["links"][0]["href"] == "https://github.com/geekan/MetaGPT/blob/main/metagpt/software_company.py"
    assert search_results[0]["position"]

    # scroll to search result
    await browser.scroll_to_search_result(search_results, index=0)

    # perceive current view
    rsp = await browser.extract_info_from_view("what is the command to run exactly?")
    assert "metagpt" in rsp

    await browser.close()


@pytest.mark.asyncio
async def test_find_links(browser):
    await browser.start()

    await browser.open_new_page(TEST_URL)
    link_info = await browser.find_links()
    assert link_info

    await browser.close()


@pytest.mark.asyncio
async def test_scroll(browser):
    await browser.start()

    await browser.open_new_page(TEST_URL)

    await browser.scroll_current_page(offset=-500)
    assert await get_scroll_position(browser.current_page) == {"x": 0, "y": 0}  # no change if you scrol up from top

    await browser.scroll_current_page(offset=500)  # scroll down
    assert await get_scroll_position(browser.current_page) == {"x": 0, "y": 500}

    await browser.scroll_current_page(offset=-200)  # scroll up
    assert await get_scroll_position(browser.current_page) == {"x": 0, "y": 300}

    await browser.close()
