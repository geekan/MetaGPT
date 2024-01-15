import pytest

from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.provider import OpenAILLM
from metagpt.schema import UserMessage
from tests.metagpt.provider.mock_llm_config import (
    mock_llm_config,
    mock_llm_config_proxy,
)


@pytest.mark.asyncio
async def test_aask_code():
    llm = LLM()
    msg = [{"role": "user", "content": "Write a python hello world code."}]
    rsp = await llm.aask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}

    logger.info(rsp)
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


@pytest.mark.asyncio
async def test_aask_code_str():
    llm = LLM()
    msg = "Write a python hello world code."
    rsp = await llm.aask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


@pytest.mark.asyncio
async def test_aask_code_message():
    llm = LLM()
    msg = UserMessage("Write a python hello world code.")
    rsp = await llm.aask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


@pytest.mark.asyncio
async def test_text_to_speech():
    llm = LLM()
    resp = await llm.atext_to_speech(
        model="tts-1",
        voice="alloy",
        input="人生说起来长，但知道一个岁月回头看，许多事件仅是仓促的。一段一段拼凑一起，合成了人生。苦难当头时，当下不免觉得是折磨；回头看，也不够是一段短短的人生旅程。",
    )
    assert 200 == resp.response.status_code


class TestOpenAI:
    def test_make_client_kwargs_without_proxy(self):
        instance = OpenAILLM(mock_llm_config)
        kwargs = instance._make_client_kwargs()
        assert kwargs == {"api_key": "mock_api_key", "base_url": "mock_base_url"}
        assert "http_client" not in kwargs

    def test_make_client_kwargs_with_proxy(self):
        instance = OpenAILLM(mock_llm_config_proxy)
        kwargs = instance._make_client_kwargs()
        assert "http_client" in kwargs
