import json


class BaseBedrockProvider(object):
    # to handle different generation kwargs
    def get_request_body(self, messages, **generate_kwargs):
        body = json.dumps(
            {"prompt": self.messages_to_prompt(messages), **generate_kwargs})
        return body

    def get_choice_text(self, response) -> str:
        response_body = self._get_response_body_json(response)
        completions = response_body["outputs"][0]['text']
        return completions

    def get_choice_text_from_stream(self, event):
        completions = json.loads(event["chunk"]["bytes"])["outputs"][0]["text"]
        return completions

    def _get_response_body_json(self, response):
        response_body = json.loads(response["body"].read())
        return response_body

    def messages_to_prompt(self, messages: list[dict]):
        """[{"role": "user", "content": msg}] to user: <msg> etc."""
        return "\n".join([f"{i['role']}: {i['content']}" for i in messages])
