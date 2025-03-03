from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from metagpt.tools.libs.image_getter import ImageGetter


@pytest.mark.asyncio
class TestImageGetter:
    @pytest_asyncio.fixture(autouse=True)
    async def image_getter_client(self):
        """Fixture to initialize the ImageGetter."""
        self.image_getter = ImageGetter(headless=True)
        await self.image_getter.start()
        yield self.image_getter
        if self.image_getter.browser_instance:
            await self.image_getter.browser_instance.close()

    @patch("metagpt.tools.libs.image_getter.decode_image")
    async def test_get_image_success(self, mock_decode_image):
        """Test successfully retrieving and saving an image."""
        search_term = "nature"
        image_save_path = Path.cwd() / "test_image_getter.jpg"

        # Mock the decode_image to avoid actual image decoding
        mock_image = AsyncMock()
        mock_decode_image.return_value = mock_image

        # Mock the Playwright page evaluation result to return a dummy base64 image string
        self.image_getter.page.goto = AsyncMock()
        self.image_getter.page.wait_for_selector = AsyncMock()
        self.image_getter.page.evaluate = AsyncMock(return_value="data:image/png;base64,FAKEBASE64STRING")

        result = await self.image_getter.get_image(search_term, str(image_save_path))

        assert f"{search_term} found." in result
        mock_decode_image.assert_called_once()
