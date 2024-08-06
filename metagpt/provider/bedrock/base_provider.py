import json
from abc import ABC, abstractmethod


class BaseBedrockProvider(ABC):
    # to handle different generation kwargs
    max_tokens_field_name = "max_tokens"

    @abstractmethod
    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        ...

    def get_request_body(self, messages: list[dict], const_kwargs, *args, **kwargs) -> str:
        body = json.dumps({"prompt": self.messages_to_prompt(messages), **const_kwargs})
        return body

    def get_choice_text(self, response_body: dict) -> str:
        completions = self._get_completion_from_dict(response_body)
        return completions

    def get_choice_text_from_stream(self, event) -> str:
        rsp_dict = json.loads(event["chunk"]["bytes"])
        completions = self._get_completion_from_dict(rsp_dict)
        return completions

    def messages_to_prompt(self, messages: list[dict]) -> str:
        """[{"role": "user", "content": msg}] to user: <msg> etc."""
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
