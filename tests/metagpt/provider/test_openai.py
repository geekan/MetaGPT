import pytest
from httpx import AsyncClient, Client

from metagpt.provider.openai_api import OpenAIGPTAPI
from metagpt.schema import UserMessage


@pytest.mark.asyncio
async def test_aask_code():
    llm = OpenAIGPTAPI()
    msg = [{"role": "user", "content": "Write a python hello world code."}]
    rsp = await llm.aask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


@pytest.mark.asyncio
async def test_aask_code_str():
    llm = OpenAIGPTAPI()
    msg = "Write a python hello world code."
    rsp = await llm.aask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


@pytest.mark.asyncio
async def test_aask_code_Message():
    llm = OpenAIGPTAPI()
    msg = UserMessage("Write a python hello world code.")
    rsp = await llm.aask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


def test_ask_code():
    llm = OpenAIGPTAPI()
    msg = [{"role": "user", "content": "Write a python hello world code."}]
    rsp = llm.ask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


def test_ask_code_str():
    llm = OpenAIGPTAPI()
    msg = "Write a python hello world code."
    rsp = llm.ask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


def test_ask_code_Message():
    llm = OpenAIGPTAPI()
    msg = UserMessage("Write a python hello world code.")
    rsp = llm.ask_code(msg)  # -> {'language': 'python', 'code': "print('Hello, World!')"}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


def test_ask_code_list_Message():
    llm = OpenAIGPTAPI()
    msg = [UserMessage("a=[1,2,5,10,-10]"), UserMessage("写出求a中最大值的代码python")]
    rsp = llm.ask_code(msg)  # -> {'language': 'python', 'code': 'max_value = max(a)\nmax_value'}
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


def test_ask_code_list_str():
    llm = OpenAIGPTAPI()
    msg = ["a=[1,2,5,10,-10]", "写出求a中最大值的代码python"]
    rsp = llm.ask_code(msg)  # -> {'language': 'python', 'code': 'max_value = max(a)\nmax_value'}
    print(rsp)
    assert "language" in rsp
    assert "code" in rsp
    assert len(rsp["code"]) > 0


def test_make_client_kwargs():
    class Config:
        openai_api_key = "test_key"
        openai_base_url = "test_url"
        openai_proxy = "http://test_proxy"

    config = Config()
    obj = OpenAIGPTAPI()
    kwargs, async_kwargs = obj._make_client_kwargs(config)

    assert kwargs["api_key"] == "test_key"
    assert kwargs["base_url"] == "test_url/"
    assert isinstance(kwargs["http_client"], Client)
    assert kwargs["http_client"].base_url == "test_url/"

    assert async_kwargs["api_key"] == "test_key"
    assert async_kwargs["base_url"] == "test_url/"
    assert isinstance(async_kwargs["http_client"], AsyncClient)
    assert async_kwargs["http_client"].base_url == "test_url/"


def test_make_client_kwargs_no_proxy():
    class Config:
        openai_api_key = "test_key"
        openai_base_url = "test_url"
        openai_proxy = None

    config = Config()
    obj = OpenAIGPTAPI()
    kwargs, async_kwargs = obj._make_client_kwargs(config)

    assert kwargs["api_key"] == "test_key"
    assert kwargs["base_url"] == "test_url/"
    assert "http_client" not in kwargs

    assert async_kwargs["api_key"] == "test_key"
    assert async_kwargs["base_url"] == "test_url/"
    assert "http_client" not in async_kwargs
