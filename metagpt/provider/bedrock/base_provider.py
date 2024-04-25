import json
from abc import ABC, abstractmethod


class BaseBedrockProvider(ABC):
    # to handle different generation kwargs
    def get_request_body(self, messages, **generate_kwargs):
        body = json.dumps(
            {"prompt": self.messages_to_prompt(messages), **generate_kwargs})
        return body

    def get_choice_text(self, response) -> str:
        response_body = self._get_response_body_json(response)
        completions = self._get_completion_from_dict(response_body)
        return completions

    def get_choice_text_from_stream(self, event):
        rsp_dict = json.loads(event["chunk"]["bytes"])
        completions = self._get_completion_from_dict(rsp_dict)
        return completions

    def _get_response_body_json(self, response):
        response_body = json.loads(response["body"].read())
        return response_body

    @abstractmethod
    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        ...

    def messages_to_prompt(self, messages: list[dict]):
        """[{"role": "user", "content": msg}] to user: <msg> etc."""
        return "\n".join([f"{i['role']}: {i['content']}" for i in messages])
