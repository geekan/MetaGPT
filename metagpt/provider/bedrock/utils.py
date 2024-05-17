from metagpt.logs import logger

# max_tokens for each model
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
    "amazon.titan-text-express-v1:0:8k": 8000,
    "amazon.titan-text-lite-v1:0:4k": 4000,
    "amazon.titan-text-lite-v1": 4000,
    "anthropic.claude-instant-v1": 100000,
    "anthropic.claude-instant-v1:2:100k": 100000,
    "anthropic.claude-v1": 100000,
    "anthropic.claude-v2": 100000,
    "anthropic.claude-v2:1": 200000,
    "anthropic.claude-v2:0:18k": 18000,
    "anthropic.claude-v2:1:200k": 200000,
    "anthropic.claude-3-sonnet-20240229-v1:0": 200000,
    "anthropic.claude-3-sonnet-20240229-v1:0:28k": 28000,
    "anthropic.claude-3-sonnet-20240229-v1:0:200k": 200000,
    "anthropic.claude-3-haiku-20240307-v1:0": 200000,
    "anthropic.claude-3-haiku-20240307-v1:0:48k": 48000,
    "anthropic.claude-3-haiku-20240307-v1:0:200k": 200000,
    # currently (2024-4-29) only available at US West (Oregon) AWS Region.
    "anthropic.claude-3-opus-20240229-v1:0": 200000,
    "cohere.command-text-v14": 4000,
    "cohere.command-text-v14:7:4k": 4000,
    "cohere.command-light-text-v14": 4000,
    "cohere.command-light-text-v14:7:4k": 4000,
    "meta.llama2-13b-chat-v1:0:4k": 4000,
    "meta.llama2-13b-chat-v1": 2000,
    "meta.llama2-70b-v1": 4000,
    "meta.llama2-70b-v1:0:4k": 4000,
    "meta.llama2-70b-chat-v1": 2000,
    "meta.llama2-70b-chat-v1:0:4k": 2000,
    "meta.llama3-8b-instruct-v1:0": 2000,
    "meta.llama3-70b-instruct-v1:0": 2000,
    "mistral.mistral-7b-instruct-v0:2": 32000,
    "mistral.mixtral-8x7b-instruct-v0:1": 32000,
    "mistral.mistral-large-2402-v1:0": 32000,
}

# TODO:use a more general function for constructing chat templates.


def messages_to_prompt_llama2(messages: list[dict]) -> str:
    BOS = ("<s>",)
    B_INST, E_INST = "[INST]", "[/INST]"
    B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"

    prompt = f"{BOS}"
    for message in messages:
        role = message.get("role", "")
        content = message.get("content", "")
        if role == "system":
            prompt += f"{B_SYS} {content} {E_SYS}"
        elif role == "user":
            prompt += f"{B_INST} {content} {E_INST}"
        elif role == "assistant":
            prompt += f"{content}"
        else:
            logger.warning(f"Unknown role name {role} when formatting messages")
            prompt += f"{content}"

    return prompt


def messages_to_prompt_llama3(messages: list[dict]) -> str:
    BOS = "<|begin_of_text|>"
    GENERAL_TEMPLATE = "<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>"

    prompt = f"{BOS}"
    for message in messages:
        role = message.get("role", "")
        content = message.get("content", "")
        prompt += GENERAL_TEMPLATE.format(role=role, content=content)

    if role != "assistant":
        prompt += "<|start_header_id|>assistant<|end_header_id|>"

    return prompt


def messages_to_prompt_claude2(messages: list[dict]) -> str:
    GENERAL_TEMPLATE = "\n\n{role}: {content}"
    prompt = ""
    for message in messages:
        role = message.get("role", "")
        content = message.get("content", "")
        prompt += GENERAL_TEMPLATE.format(role=role, content=content)

    if role != "assistant":
        prompt += "\n\nAssistant:"

    return prompt


def get_max_tokens(model_id: str) -> int:
    try:
        max_tokens = (NOT_SUUPORT_STREAM_MODELS | SUPPORT_STREAM_MODELS)[model_id]
    except KeyError:
        logger.warning(f"Couldn't find model:{model_id} , max tokens has been set to 2048")
        max_tokens = 2048
    return max_tokens
