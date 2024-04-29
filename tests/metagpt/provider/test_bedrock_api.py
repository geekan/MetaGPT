import pytest
import json
from metagpt.provider.bedrock_api import BedrockLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_bedrock
from metagpt.provider.bedrock.utils import get_max_tokens, SUPPORT_STREAM_MODELS, NOT_SUUPORT_STREAM_MODELS
from tests.metagpt.provider.req_resp_const import BEDROCK_PROVIDER_REQUEST_BODY, BEDROCK_PROVIDER_RESPONSE_BODY

# all available model from bedrock
models = (SUPPORT_STREAM_MODELS | NOT_SUUPORT_STREAM_MODELS)
messages = [{"role": "user", "content": "Hi!"}]


def mock_bedrock_provider_response(self, *args, **kwargs) -> dict:
    provider = self.config.model.split(".")[0]
    return BEDROCK_PROVIDER_RESPONSE_BODY[provider]


def mock_bedrock_provider_stream_response(self, *args, **kwargs) -> dict:
    # use json object to mock EventStream
    def dict2bytes(x):
        return json.dumps(x).encode("utf-8")
    provider = self.config.model.split(".")[0]

    if provider == "amazon":
        response_body_bytes = dict2bytes({"outputText": "Hello World"})
    elif provider == "anthropic":
        response_body_bytes = dict2bytes({"type": "content_block_delta", "index": 0,
                                          "delta": {"type": "text_delta", "text": "Hello World"}})
    elif provider == "cohere":
        response_body_bytes = dict2bytes(
            {"is_finished": False, "text": "Hello World"})
    else:
        response_body_bytes = dict2bytes(
            BEDROCK_PROVIDER_RESPONSE_BODY[provider])

    response_body_stream = {
        "body": [{"chunk": {"bytes": response_body_bytes}}]}
    return response_body_stream


def get_bedrock_request_body(model_id) -> dict:
    provider = model_id.split(".")[0]
    return BEDROCK_PROVIDER_REQUEST_BODY[provider]


def is_subset(subset, superset) -> bool:
    """Ensure all fields in request body are allowed.

    ```python
    subset = {"prompt": "hello","kwargs": {"temperature": 0.9,"p": 0.0}}
    superset = {"prompt": "hello", "kwargs": {"temperature": 0.0, "top-p": 0.0}}
    is_subset(subset, superset)
    ```
    >>>False
    """
    for key, value in subset.items():
        if key not in superset:
            return False
        if isinstance(value, dict):
            if not isinstance(superset[key], dict):
                return False
            if not is_subset(value, superset[key]):
                return False
    return True


@pytest.fixture(scope="class", params=models)
def bedrock_api(request) -> BedrockLLM:
    model_id = request.param
    mock_llm_config_bedrock.model = model_id
    api = BedrockLLM(mock_llm_config_bedrock)
    return api


class TestBedrockAPI:
    def _patch_invoke_model(self, mocker):
        mocker.patch("metagpt.provider.bedrock_api.BedrockLLM.invoke_model", mock_bedrock_provider_response)

    def _patch_invoke_model_stream(self, mocker):
        mocker.patch("metagpt.provider.bedrock_api.BedrockLLM.invoke_model_with_response_stream",
                     mock_bedrock_provider_stream_response)

    def test_const_kwargs(self, bedrock_api: BedrockLLM):
        provider = bedrock_api.provider
        assert bedrock_api._const_kwargs[provider.max_tokens_field_name] <= get_max_tokens(
            bedrock_api.config.model)

    def test_get_request_body(self, bedrock_api: BedrockLLM):
        """Ensure request body has correct format"""
        provider = bedrock_api.provider
        request_body = json.loads(provider.get_request_body(
            messages, bedrock_api._const_kwargs))

        assert is_subset(request_body, get_bedrock_request_body(bedrock_api.config.model))

    def test_completion(self, bedrock_api: BedrockLLM, mocker):
        self._patch_invoke_model(mocker)
        assert bedrock_api.completion(messages) == "Hello World"

    def test_chat_completion_stream(self, bedrock_api: BedrockLLM, mocker):
        self._patch_invoke_model(mocker)
        self._patch_invoke_model_stream(mocker)
        assert bedrock_api._chat_completion_stream(messages) == "Hello World"

    @pytest.mark.asyncio
    async def test_achat_completion_stream(self, bedrock_api: BedrockLLM, mocker):
        self._patch_invoke_model_stream(mocker)
        self._patch_invoke_model(mocker)
        assert await bedrock_api._achat_completion_stream(messages) == "Hello World"

    @pytest.mark.asyncio
    async def test_acompletion(self, bedrock_api: BedrockLLM, mocker):
        self._patch_invoke_model(mocker)
        assert await bedrock_api.acompletion(messages) == "Hello World"
