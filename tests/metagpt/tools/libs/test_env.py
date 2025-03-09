import os
from unittest.mock import AsyncMock

import pytest

from metagpt.tools.libs.env import (
    EnvKeyNotFoundError,
    default_get_env_description,
    get_env,
    get_env_default,
    set_get_env_entry,
)


@pytest.mark.asyncio
class TestEnv:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for environment variables."""
        self.mock_os_env = {
            "TEST_APP-KEY": "value1",
            "TEST_APP_KEY": "value2",
        }
        os.environ.update(self.mock_os_env)
        yield
        # Clear added environment variables
        for key in self.mock_os_env.keys():
            del os.environ[key]

    async def test_get_env(self):
        """Test retrieving an environment variable."""
        result = await get_env("KEY", app_name="TEST_APP")
        assert result == "value1"

        with pytest.raises(EnvKeyNotFoundError):
            await get_env("NON_EXISTENT_KEY")

        # Using no app_name
        result = await get_env("TEST_APP_KEY")
        assert result == "value2"

    async def test_get_env_default(self):
        """Test retrieving environment variable with default value."""
        result = await get_env_default("NON_EXISTENT_KEY", app_name="TEST_APP", default_value="default")
        assert result == "default"

    async def test_get_env_description(self):
        """Test retrieving descriptions for environment variables."""
        descriptions = await default_get_env_description()

        assert 'await get_env(key="KEY", app_name="TEST_APP")' in descriptions
        assert (
            descriptions['await get_env(key="KEY", app_name="TEST_APP")']
            == "Return the value of environment variable `TEST_APP-KEY`."
        )

    async def test_set_get_env_entry(self):
        """Test overriding get_env functionality."""
        mock_get_env_value = "mocked_value"
        mock_func = AsyncMock(return_value=mock_get_env_value)
        set_get_env_entry(mock_func, default_get_env_description)

        result = await get_env("set_get_env")
        assert result == mock_get_env_value
