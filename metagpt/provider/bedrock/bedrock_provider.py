import json
from typing import Literal, Tuple, Union

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
    #     https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-37.html
    #     https://docs.aws.amazon.com/code-library/latest/ug/python_3_bedrock-runtime_code_examples.html#anthropic_claude

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
        if self.reasoning:
            generate_kwargs["temperature"] = 1  # should be 1
            generate_kwargs["thinking"] = {"type": "enabled", "budget_tokens": self.reasoning_max_token}

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

    def _get_completion_from_dict(self, rsp_dict: dict) -> dict[str, Tuple[str, str]]:
        if self.reasoning:
            return {"reasoning_content": rsp_dict["content"][0]["thinking"], "content": rsp_dict["content"][1]["text"]}
        return rsp_dict["content"][0]["text"]

    def get_choice_text_from_stream(self, event) -> Union[bool, str]:
        # https://docs.anthropic.com/claude/reference/messages-streaming
        rsp_dict = json.loads(event["chunk"]["bytes"])
        if rsp_dict["type"] == "content_block_delta":
            reasoning = False
            delta_type = rsp_dict["delta"]["type"]
            if delta_type == "text_delta":
                completions = rsp_dict["delta"]["text"]
            elif delta_type == "thinking_delta":
                completions = rsp_dict["delta"]["thinking"]
                reasoning = True
            elif delta_type == "signature_delta":
                completions = ""
            return reasoning, completions
        elif rsp_dict["type"] == "message_stop":
            self.usage = {
                "prompt_tokens": rsp_dict.get("amazon-bedrock-invocationMetrics", {}).get("inputTokenCount", 0),
                "completion_tokens": rsp_dict.get("amazon-bedrock-invocationMetrics", {}).get("outputTokenCount", 0),
            }
        return False, ""


class CohereProvider(BaseBedrockProvider):
    # For more information, see
    # (Command) https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command.html
    # (Command R/R+) https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command-r-plus.html

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["generations"][0]["text"]

    def messages_to_prompt(self, messages: list[dict]) -> str:
        if "command-r" in self.model_name:
            role_map = {"user": "USER", "assistant": "CHATBOT", "system": "USER"}
            messages = list(
                map(lambda message: {"role": role_map[message["role"]], "message": message["content"]}, messages)
            )
            return messages
        else:
            """[{"role": "user", "content": msg}] to user: <msg> etc."""
            return "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    def get_request_body(self, messages: list[dict], generate_kwargs, *args, **kwargs):
        prompt = self.messages_to_prompt(messages)
        if "command-r" in self.model_name:
            chat_history, message = prompt[:-1], prompt[-1]["message"]
            body = json.dumps({"message": message, "chat_history": chat_history, **generate_kwargs})
        else:
            body = json.dumps({"prompt": prompt, "stream": kwargs.get("stream", False), **generate_kwargs})
        return body

    def get_choice_text_from_stream(self, event) -> Union[bool, str]:
        rsp_dict = json.loads(event["chunk"]["bytes"])
        completions = rsp_dict.get("text", "")
        return False, completions


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

    def __init__(self, model_type: Literal["j2", "jamba"]) -> None:
        self.model_type = model_type
        if self.model_type == "j2":
            self.max_tokens_field_name = "maxTokens"
        else:
            self.max_tokens_field_name = "max_tokens"

    def get_request_body(self, messages: list[dict], generate_kwargs, *args, **kwargs) -> str:
        if self.model_type == "j2":
            body = super().get_request_body(messages, generate_kwargs, *args, **kwargs)
        else:
            body = json.dumps(
                {
                    "messages": messages,
                    **generate_kwargs,
                }
            )
        return body

    def get_choice_text_from_stream(self, event) -> Union[bool, str]:
        rsp_dict = json.loads(event["chunk"]["bytes"])
        completions = rsp_dict.get("choices", [{}])[0].get("delta", {}).get("content", "")
        return False, completions

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        if self.model_type == "j2":
            # See https://docs.ai21.com/reference/j2-complete-ref
            return rsp_dict["completions"][0]["data"]["text"]
        else:
            # See https://docs.ai21.com/reference/jamba-instruct-api
            return rsp_dict["choices"][0]["message"]["content"]


class AmazonProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-text.html

    max_tokens_field_name = "maxTokenCount"

    def get_request_body(self, messages: list[dict], generate_kwargs, *args, **kwargs):
        body = json.dumps({"inputText": self.messages_to_prompt(messages), "textGenerationConfig": generate_kwargs})
        return body

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["results"][0]["outputText"]

    def get_choice_text_from_stream(self, event) -> Union[bool, str]:
        rsp_dict = json.loads(event["chunk"]["bytes"])
        completions = rsp_dict["outputText"]
        return False, completions


PROVIDERS = {
    "mistral": MistralProvider,
    "meta": MetaProvider,
    "ai21": Ai21Provider,
    "cohere": CohereProvider,
    "anthropic": AnthropicProvider,
    "amazon": AmazonProvider,
}


def get_provider(model_id: str, reasoning: bool = False, reasoning_max_token: int = 4000):
    arr = model_id.split(".")
    if len(arr) == 2:
        provider, model_name = arr  # meta、mistral……
    elif len(arr) == 3:
        # some model_ids may contain country like us.xx.xxx
        _, provider, model_name = arr

    if provider not in PROVIDERS:
        raise KeyError(f"{provider} is not supported!")
    if provider == "meta":
        # distinguish llama2 and llama3
        return PROVIDERS[provider](model_name[:6])
    elif provider == "ai21":
        # distinguish between j2 and jamba
        return PROVIDERS[provider](model_name.split("-")[0])
    elif provider == "cohere":
        # distinguish between R/R+ and older models
        return PROVIDERS[provider](model_name)
    return PROVIDERS[provider](reasoning=reasoning, reasoning_max_token=reasoning_max_token)
