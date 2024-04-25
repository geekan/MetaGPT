import json


class BaseBedrockProvider(object):
    # to handle different generation kwargs
    def get_request_body(self, messages, **generate_kwargs):
        return json.dumps({"prompt": self.messages_to_prompt(messages)} | generate_kwargs)

    def get_choice_text(self, response) -> str:
        response_body = json.loads(response["body"].read())
        completions = response_body["outputs"][0]['text']
        return completions

    def messages_to_prompt(self, messages: list[dict]):
        """[{"role": "user", "content": msg}] to user: <msg> etc."""
        return "\n".join([f"{i['role']}: {i['content']}" for i in messages])

    def format_prompt(self, prompt: str) -> str:
        return prompt

    def format_messages(self, messages: list[dict]) -> list[dict]:
        return messages
