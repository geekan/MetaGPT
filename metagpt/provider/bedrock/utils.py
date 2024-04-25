from metagpt.logs import logger

def messages_to_prompt_llama(messages: list[dict]):
    BOS, EOS = "<s>", "</s>"
    B_INST, E_INST = "[INST]", "[/INST]"
    B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"

    prompt = f"{BOS}"
    for message in messages:
        role = message["role"]
        content = message["content"]
        if role == "system":
            prompt += f"{B_SYS} {content} {E_SYS}"
        elif role == "user":
            prompt += f"{B_INST} {content} {E_INST}"
        elif role == "assistant":
            prompt += f"{content}"
        else:
            logger.warning(
                f"Unknown role name {role} when formatting messages")
            prompt += f"{content}"

    return prompt


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
