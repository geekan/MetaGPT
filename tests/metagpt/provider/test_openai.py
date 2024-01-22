from unittest.mock import Mock

import pytest
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import Function

from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.provider.openai_api import OpenAILLM

CONFIG.openai_proxy = None


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

    @pytest.fixture
    def tool_calls_rsp(self):
        function_rsps = [
            Function(arguments='{\n"language": "python",\n"code": "print(\'hello world\')"', name="execute"),
            Function(arguments='{\n"language": "python",\n"code": ```print("hello world")```', name="execute"),
            Function(arguments='{\n"language": "python",\n"code": \'print("hello world")\'', name="execute"),
            Function(arguments='{\n"language": \'python\',\n"code": "print(\'hello world\')"', name="execute"),
            Function(arguments='\nprint("hello world")\\n', name="execute"),
        ]
        tool_calls = [
            ChatCompletionMessageToolCall(type="function", id=f"call_{i}", function=f)
            for i, f in enumerate(function_rsps)
        ]
        messages = [ChatCompletionMessage(content=None, role="assistant", tool_calls=[t]) for t in tool_calls]
        # 添加一个纯文本响应
        messages.append(
            ChatCompletionMessage(content="Completed a python code for hello world!", role="assistant", tool_calls=None)
        )
        choices = [
            Choice(finish_reason="tool_calls", logprobs=None, index=i, message=msg) for i, msg in enumerate(messages)
        ]
        return [
            ChatCompletion(id=str(i), choices=[c], created=i, model="gpt-4", object="chat.completion")
            for i, c in enumerate(choices)
        ]

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

    def test_get_choice_function_arguments_for_aask_code(self, tool_calls_rsp):
        instance = OpenAILLM()
        for i, rsp in enumerate(tool_calls_rsp):
            code = instance.get_choice_function_arguments(rsp)
            logger.info(f"\ntest get function call arguments {i}: {code}")
            assert "code" in code
            assert "language" in code
            assert "hello world" in code["code"]

            if "Completed a python code for hello world!" == code["code"]:
                code["language"] == "markdown"
            else:
                code["language"] == "python"
