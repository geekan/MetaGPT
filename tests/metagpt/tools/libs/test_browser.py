from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from metagpt.const import TEST_DATA_PATH
from metagpt.tools.libs.browser import Browser

TEST_URL = "https://docs.deepwisdom.ai/main/en/guide/get_started/quickstart.html"

TEST_SCREENSHOT_PATH = TEST_DATA_PATH / "screenshot.png"


@pytest.mark.asyncio
class TestBrowser:
    test_url = "https://juejin.cn/"

    @pytest_asyncio.fixture(autouse=True)
    async def browser_client(self):
        """Setup before each test case."""
        print("browser_client")
        browser = await self.async_setup()
        yield browser
        await self.browser.stop()

    async def async_setup(self):
        self.browser = Browser(headless=True)
        await self.browser.start()
        return self.browser

    async def async_teardown(self):
        """Teardown after each test case."""
        await self.browser.stop()

    async def test_start_and_stop(self):
        """Test browser start and stop functionality."""
        assert self.browser.playwright is not None
        assert self.browser.browser_instance is not None
        assert self.browser.browser_ctx is not None
        assert self.browser.page is not None

        await self.async_teardown()

        assert self.browser.playwright is None
        assert self.browser.browser_instance is None
        assert self.browser.browser_ctx is None

    async def test_goto(self):
        """Test navigating to a URL."""
        mock_reporter = AsyncMock()
        self.browser.reporter = mock_reporter

        result = await self.browser.goto(self.test_url)
        assert "SUCCESS" in result
        assert self.test_url in self.browser.page.url

    @patch("metagpt.tools.libs.browser.click_element", new_callable=AsyncMock)
    async def test_click(self, mock_click_element):
        """Test clicking on an element."""
        self.browser.accessibility_tree = [
            {"nodeId": "1", "backendDOMNodeId": 101, "name": "Button"},
            {"nodeId": "2", "backendDOMNodeId": 102, "name": "Input"},
        ]
        self.browser.page = AsyncMock()

        await self.browser.click(1)

        mock_click_element.assert_called_once()

    @patch("metagpt.tools.libs.browser.click_element", new_callable=AsyncMock)
    @patch("metagpt.tools.libs.browser.type_text", new_callable=AsyncMock)
    async def test_type(self, mock_type_text, mock_click_element):
        """Test typing text into an input field."""
        content = "Hello, world!"
        self.browser.accessibility_tree = [
            {"nodeId": "1", "backendDOMNodeId": 101, "name": "Button"},
            {"nodeId": "2", "backendDOMNodeId": 102, "name": "Input"},
        ]
        self.browser.page = AsyncMock()

        await self.browser.type(1, content)

        mock_click_element.assert_called_once()
        mock_type_text.assert_called_once_with(self.browser.page, content)

    @patch("metagpt.tools.libs.browser.key_press", new_callable=AsyncMock)
    @patch("metagpt.tools.libs.browser.hover_element", new_callable=AsyncMock)
    async def test_hover_press(self, mock_hover_element, mock_key_press):
        """Test Hover and press key"""
        self.browser.accessibility_tree = [
            {"nodeId": "1", "backendDOMNodeId": 101, "name": "Button"},
            {"nodeId": "2", "backendDOMNodeId": 102, "name": "Input"},
        ]
        self.browser.page = AsyncMock()

        key_comb = "Enter"
        await self.browser.hover(1)
        await self.browser.press(key_comb)
        mock_hover_element.assert_called_once()
        mock_key_press.assert_called_once_with(self.browser.page, key_comb)

    async def test_scroll(self):
        """Scroll the page up or down."""
        await self.browser.scroll("down")
        await self.browser.scroll("up")

    async def test_go_back_and_forward(self):
        await self.browser.go_back()
        await self.browser.go_forward()

    async def test_tab_focus(self):
        await self.browser.tab_focus(0)

    async def test_close_tab(self):
        """Test closing a tab."""
        mock_close = AsyncMock()
        self.browser.page = AsyncMock()
        self.browser.page.close = mock_close

        await self.browser.close_tab()

        mock_close.assert_called_once()
