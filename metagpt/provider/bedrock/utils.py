from metagpt.logs import logger

NOT_SUUPORT_STREAM_MODELS = {
    "ai21.j2-grande-instruct": 8000,
    "ai21.j2-jumbo-instruct": 8000,
    "ai21.j2-mid": 8000,
    "ai21.j2-mid-v1": 8000,
    "ai21.j2-ultra": 8000,
    "ai21.j2-ultra-v1": 8000,
}

SUPPORT_STREAM_MODELS = {
    "amazon.titan-tg1-large": 8000,
    "amazon.titan-text-express-v1": 8000,
    "anthropic.claude-instant-v1": 100000,
    "anthropic.claude-v1": 100000,
    "anthropic.claude-v2": 100000,
    "anthropic.claude-v2:1": 200000,
    "anthropic.claude-3-sonnet-20240229-v1:0": 200000,
    "anthropic.claude-3-haiku-20240307-v1:0": 200000,
    "anthropic.claude-3-opus-20240229-v1:0": 200000,
    "cohere.command-text-v14": 4096,
    "cohere.command-light-text-v14": 4096,
    "meta.llama2-70b-v1": 4096,
    "meta.llama3-8b-instruct-v1:0": 2000,
    "meta.llama3-70b-instruct-v1:0": 2000,
    "mistral.mistral-7b-instruct-v0:2": 32000,
    "mistral.mixtral-8x7b-instruct-v0:1": 32000,
    "mistral.mistral-large-2402-v1:0": 32000,
}


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


def get_max_tokens(model_id) -> int:
    return (NOT_SUUPORT_STREAM_MODELS | SUPPORT_STREAM_MODELS)[model_id]


