import pytest
import json
from metagpt.provider.bedrock.amazon_bedrock_api import AmazonBedrockLLM
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
    response_body_bytes = dict2bytes(BEDROCK_PROVIDER_RESPONSE_BODY[provider])
    # decoded bytes share the same format as non-stream response_body except for titan
    if provider == "amazon":
        response_body_stream = {
            "body": [{'chunk': {'bytes': dict2bytes({"outputText": "Hello World"})}}]}
    else:
        response_body_stream = {
            "body": [{'chunk': {'bytes': response_body_bytes}}]}
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
def bedrock_api(request) -> AmazonBedrockLLM:
    model_id = request.param
    mock_llm_config_bedrock.model = model_id
    api = AmazonBedrockLLM(mock_llm_config_bedrock)
    return api


class TestAPI:
    def test_generate_kwargs(self, bedrock_api: AmazonBedrockLLM):
        provider = bedrock_api._get_provider()
        assert bedrock_api._generate_kwargs[provider.max_tokens_field_name] <= get_max_tokens(
            bedrock_api.config.model)

    def test_get_request_body(self, bedrock_api: AmazonBedrockLLM):
        """Ensure request body has correct format"""
        provider = bedrock_api._get_provider()
        request_body = json.loads(provider.get_request_body(
            messages, **bedrock_api._generate_kwargs))

        assert is_subset(request_body, get_bedrock_request_body(
            bedrock_api.config.model))

    def test_completion(self, bedrock_api: AmazonBedrockLLM, mocker):
        mocker.patch("metagpt.provider.bedrock.amazon_bedrock_api.AmazonBedrockLLM.invoke_model",
                     mock_bedrock_provider_response)
        assert bedrock_api.completion(messages) == "Hello World"

    def test_stream_completion(self, bedrock_api: AmazonBedrockLLM, mocker):
        mocker.patch("metagpt.provider.bedrock.amazon_bedrock_api.AmazonBedrockLLM.invoke_model",
                     mock_bedrock_provider_response)
        mocker.patch("metagpt.provider.bedrock.amazon_bedrock_api.AmazonBedrockLLM.invoke_model_with_response_stream",
                     mock_bedrock_provider_stream_response)
        assert bedrock_api._chat_completion_stream(messages) == "Hello World"
