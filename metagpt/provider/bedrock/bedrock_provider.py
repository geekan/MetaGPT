from metagpt.provider.bedrock.base_provider import BaseBedrockProvider
import json


class MistralProvider(BaseBedrockProvider):

    def format_prompt(self, prompt: str) -> str:
        # for mixtral and llama
        return f"<s>[INST]{prompt}[/INST]"

    def get_request_body(self, messages, **generate_kwargs):
        return json.dumps({"prompt": self.format_prompt(self.messages_to_prompt(messages))} | generate_kwargs)


class AnthropicProvider(BaseBedrockProvider):
    pass


class CohereProvider(BaseBedrockProvider):
    pass


class MetaProvider(BaseBedrockProvider):
    pass


class Ai21Provider(BaseBedrockProvider):
    pass


PROVIDERS = {
    "mistral": MistralProvider()
}

NOT_SUUPORT_STREAM_MODELS = {
    "ai21.j2-grande-instruct",
    "ai21.j2-jumbo-instruct",
    "ai21.j2-mid",
    "ai21.j2-mid-v1",
    "ai21.j2-ultra",
    "ai21.j2-ultra-v1",
}

SUPPORT_STREAM_MODELS = {
    "amazon.titan-tg1-large",
    "amazon.titan-text-lite-v1:0:4k",
    "amazon.titan-text-lite-v1",
    "amazon.titan-text-express-v1:0:8k",
    "amazon.titan-text-express-v1",
    "anthropic.claude-instant-v1:2:100k",
    "anthropic.claude-instant-v1",
    "anthropic.claude-v2:0:18k",
    "anthropic.claude-v2:0:100k",
    "anthropic.claude-v2:1:18k",
    "anthropic.claude-v2:1:200k",
    "anthropic.claude-v2:1",
    "anthropic.claude-v2:2:18k",
    "anthropic.claude-v2:2:200k",
    "anthropic.claude-v2:2",
    "anthropic.claude-v2",
    "anthropic.claude-3-sonnet-20240229-v1:0:28k",
    "anthropic.claude-3-sonnet-20240229-v1:0:200k",
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0:48k",
    "anthropic.claude-3-haiku-20240307-v1:0:200k",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "cohere.command-text-v14:7:4k",
    "cohere.command-text-v14",
    "cohere.command-light-text-v14:7:4k",
    "cohere.command-light-text-v14",
    "meta.llama2-70b-v1",
    "meta.llama3-8b-instruct-v1:0",
    "meta.llama3-70b-instruct-v1:0",
    "mistral.mistral-7b-instruct-v0:2",
    "mistral.mixtral-8x7b-instruct-v0:1",
    "mistral.mistral-large-2402-v1:0",
}


def get_provider(model_id: str):
    model_name = model_id.split(".")[0]  # meta、mistral……
    if model_name not in PROVIDERS:
        raise KeyError(f"{model_name} is not supported!")
    return PROVIDERS[model_name]
