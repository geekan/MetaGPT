import json
from metagpt.provider.bedrock.base_provider import BaseBedrockProvider
from metagpt.provider.bedrock.utils import messages_to_prompt_llama


class MistralProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-mistral.html

    def messages_to_prompt(self, messages: list[dict]):
        return messages_to_prompt_llama(messages)

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["outputs"][0]["text"]


class AnthropicProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html

    def get_request_body(self, messages, **generate_kwargs):
        body = json.dumps(
            {"messages": messages, "anthropic_version": "bedrock-2023-05-31", **generate_kwargs})
        return body

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["content"][0]["text"]


class CohereProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command.html

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["generations"][0]["text"]


class MetaProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-meta.html

    def messages_to_prompt(self, messages: list[dict]):
        return messages_to_prompt_llama(messages)

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["generation"]


class Ai21Provider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-jurassic2.html

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict['completions'][0]["data"]["text"]


PROVIDERS = {
    "mistral": MistralProvider(),
    "meta": MetaProvider(),
    "ai21": Ai21Provider(),
    "cohere": CohereProvider(),
    "anthropic": AnthropicProvider(),
}


def get_provider(model_id: str):
    model_name = model_id.split(".")[0]  # meta、mistral……
    if model_name not in PROVIDERS:
        raise KeyError(f"{model_name} is not supported!")
    return PROVIDERS[model_name]
