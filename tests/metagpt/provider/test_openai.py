from unittest.mock import Mock

import pytest

from metagpt.config import CONFIG
from metagpt.provider.openai_api import OpenAILLM
from metagpt.schema import UserMessage

CONFIG.openai_proxy = None


@pytest.mark.asyncio
async def test_aask_code():
    llm = OpenAILLM()
    msg = [{"role": "user", "content": "Write a python hello world code."}]
    rsp = await llm.aask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


@pytest.mark.asyncio
async def test_aask_code_str():
    llm = OpenAILLM()
    msg = "Write a python hello world code."
    rsp = await llm.aask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


@pytest.mark.asyncio
async def test_aask_code_Message():
    llm = OpenAILLM()
    msg = UserMessage("Write a python hello world code.")
    rsp = await llm.aask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


class TestOpenAI:
    @pytest.fixture
    def config(self):
        return Mock(
            openai_api_key="test_key",
            OPENAI_API_KEY="test_key",
            openai_base_url="test_url",
            OPENAI_BASE_URL="test_url",
            openai_proxy=None,
            openai_api_type="other",
        )

    @pytest.fixture
    def config_azure(self):
        return Mock(
            openai_api_key="test_key",
            OPENAI_API_KEY="test_key",
            openai_api_version="test_version",
            openai_base_url="test_url",
            OPENAI_BASE_URL="test_url",
            openai_proxy=None,
            openai_api_type="azure",
        )

    @pytest.fixture
    def config_proxy(self):
        return Mock(
            openai_api_key="test_key",
            OPENAI_API_KEY="test_key",
            openai_base_url="test_url",
            OPENAI_BASE_URL="test_url",
            openai_proxy="http://proxy.com",
            openai_api_type="other",
        )

    @pytest.fixture
    def config_azure_proxy(self):
        return Mock(
            openai_api_key="test_key",
            OPENAI_API_KEY="test_key",
            openai_api_version="test_version",
            openai_base_url="test_url",
            OPENAI_BASE_URL="test_url",
            openai_proxy="http://proxy.com",
            openai_api_type="azure",
        )

    def test_make_client_kwargs_without_proxy(self, config):
        instance = OpenAILLM()
        instance.config = config
        kwargs = instance._make_client_kwargs()
        assert kwargs == {"api_key": "test_key", "base_url": "test_url"}
        assert "http_client" not in kwargs

    def test_make_client_kwargs_without_proxy_azure(self, config_azure):
        instance = OpenAILLM()
        instance.config = config_azure
        kwargs = instance._make_client_kwargs()
        assert kwargs == {"api_key": "test_key", "base_url": "test_url"}
        assert "http_client" not in kwargs

    def test_make_client_kwargs_with_proxy(self, config_proxy):
        instance = OpenAILLM()
        instance.config = config_proxy
        kwargs = instance._make_client_kwargs()
        assert "http_client" in kwargs

    def test_make_client_kwargs_with_proxy_azure(self, config_azure_proxy):
        instance = OpenAILLM()
        instance.config = config_azure_proxy
        kwargs = instance._make_client_kwargs()
        assert "http_client" in kwargs
