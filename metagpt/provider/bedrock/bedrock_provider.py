import json
from typing import Literal, Tuple

from metagpt.provider.bedrock.base_provider import BaseBedrockProvider
from metagpt.provider.bedrock.utils import (
    messages_to_prompt_llama2,
    messages_to_prompt_llama3,
)


class MistralProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-mistral.html

    def messages_to_prompt(self, messages: list[dict]):
        return messages_to_prompt_llama2(messages)

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["outputs"][0]["text"]


class AnthropicProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html

    def _split_system_user_messages(self, messages: list[dict]) -> Tuple[str, list[dict]]:
        system_messages = []
        user_messages = []
        for message in messages:
            if message["role"] == "system":
                system_messages.append(message)
            else:
                user_messages.append(message)
        return self.messages_to_prompt(system_messages), user_messages

    def get_request_body(self, messages: list[dict], generate_kwargs, *args, **kwargs) -> str:
        system_message, user_messages = self._split_system_user_messages(messages)
        body = json.dumps(
            {
                "messages": user_messages,
                "anthropic_version": "bedrock-2023-05-31",
                "system": system_message,
                **generate_kwargs,
            }
        )
        return body

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["content"][0]["text"]

    def get_choice_text_from_stream(self, event) -> str:
        # https://docs.anthropic.com/claude/reference/messages-streaming
        rsp_dict = json.loads(event["chunk"]["bytes"])
        if rsp_dict["type"] == "content_block_delta":
            completions = rsp_dict["delta"]["text"]
            return completions
        else:
            return ""


class CohereProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command.html

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["generations"][0]["text"]

    def get_request_body(self, messages: list[dict], generate_kwargs, *args, **kwargs):
        body = json.dumps(
            {"prompt": self.messages_to_prompt(messages), "stream": kwargs.get("stream", False), **generate_kwargs}
        )
        return body

    def get_choice_text_from_stream(self, event) -> str:
        rsp_dict = json.loads(event["chunk"]["bytes"])
        completions = rsp_dict.get("text", "")
        return completions


class MetaProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-meta.html

    max_tokens_field_name = "max_gen_len"

    def __init__(self, llama_version: Literal["llama2", "llama3"]) -> None:
        self.llama_version = llama_version

    def messages_to_prompt(self, messages: list[dict]):
        if self.llama_version == "llama2":
            return messages_to_prompt_llama2(messages)
        else:
            return messages_to_prompt_llama3(messages)

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["generation"]


class Ai21Provider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-jurassic2.html

    max_tokens_field_name = "maxTokens"

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["completions"][0]["data"]["text"]


class AmazonProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-text.html

    max_tokens_field_name = "maxTokenCount"

    def get_request_body(self, messages: list[dict], generate_kwargs, *args, **kwargs):
        body = json.dumps({"inputText": self.messages_to_prompt(messages), "textGenerationConfig": generate_kwargs})
        return body

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["results"][0]["outputText"]

    def get_choice_text_from_stream(self, event) -> str:
        rsp_dict = json.loads(event["chunk"]["bytes"])
        completions = rsp_dict["outputText"]
        return completions


PROVIDERS = {
    "mistral": MistralProvider,
    "meta": MetaProvider,
    "ai21": Ai21Provider,
    "cohere": CohereProvider,
    "anthropic": AnthropicProvider,
    "amazon": AmazonProvider,
}


def get_provider(model_id: str):
    provider, model_name = model_id.split(".")[0:2]  # meta、mistral……
    if provider not in PROVIDERS:
        raise KeyError(f"{provider} is not supported!")
    if provider == "meta":
        # distinguish llama2 and llama3
        return PROVIDERS[provider](model_name[:6])
    return PROVIDERS[provider]()
