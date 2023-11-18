import pytest

from metagpt.provider.openai_api import OpenAIGPTAPI


@pytest.mark.asyncio
async def test_aask_code():
    llm = OpenAIGPTAPI()
    msg = [{"role": "user", "content": "Write a python hello world code."}]
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
