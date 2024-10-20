from metagpt.logs import logger

# max_tokens for each model
NOT_SUPPORT_STREAM_MODELS = {
    # Jurassic-2 Mid-v1 and Ultra-v1
    # + Legacy date: 2024-04-30 (us-west-2/Oregon)
    # + EOL date: 2024-08-31 (us-west-2/Oregon)
    "ai21.j2-mid-v1": 8191,
    "ai21.j2-ultra-v1": 8191,
}

SUPPORT_STREAM_MODELS = {
    # Jamba-Instruct
    # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-jamba.html
    "ai21.jamba-instruct-v1:0": 4096,
    # Titan Text G1 - Lite
    # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-text.html
    "amazon.titan-text-lite-v1:0:4k": 4096,
    "amazon.titan-text-lite-v1": 4096,
    # Titan Text G1 - Express
    "amazon.titan-text-express-v1": 8192,
    "amazon.titan-text-express-v1:0:8k": 8192,
    # Titan Text Premier
    "amazon.titan-text-premier-v1:0": 3072,
    "amazon.titan-text-premier-v1:0:32k": 3072,
    # Claude Instant v1
    # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-text-completion.html
    # https://docs.anthropic.com/en/docs/about-claude/models#model-comparison
    "anthropic.claude-instant-v1": 4096,
    "anthropic.claude-instant-v1:2:100k": 4096,
    # Claude v2
    "anthropic.claude-v2": 4096,
    "anthropic.claude-v2:0:18k": 4096,
    "anthropic.claude-v2:0:100k": 4096,
    # Claude v2.1
    "anthropic.claude-v2:1": 4096,
    "anthropic.claude-v2:1:18k": 4096,
    "anthropic.claude-v2:1:200k": 4096,
    # Claude 3 Sonnet
    "anthropic.claude-3-sonnet-20240229-v1:0": 4096,
    "anthropic.claude-3-sonnet-20240229-v1:0:28k": 4096,
    "anthropic.claude-3-sonnet-20240229-v1:0:200k": 4096,
    # Claude 3 Haiku
    "anthropic.claude-3-haiku-20240307-v1:0": 4096,
    "anthropic.claude-3-haiku-20240307-v1:0:48k": 4096,
    "anthropic.claude-3-haiku-20240307-v1:0:200k": 4096,
    # Claude 3 Opus
    "anthropic.claude-3-opus-20240229-v1:0": 4096,
    # Claude 3.5 Sonnet
    "anthropic.claude-3-5-sonnet-20240620-v1:0": 8192,
    # Command Text
    # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command.html
    "cohere.command-text-v14": 4096,
    "cohere.command-text-v14:7:4k": 4096,
    # Command Light Text
    "cohere.command-light-text-v14": 4096,
    "cohere.command-light-text-v14:7:4k": 4096,
    # Command R
    # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command-r-plus.html
    "cohere.command-r-v1:0": 4096,
    # Command R+
    "cohere.command-r-plus-v1:0": 4096,
    # Llama 2 (--> Llama 3/3.1/3.2) !!!
    # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-meta.html
    # + Legacy: 2024-05-12
    # + EOL: 2024-10-30
    # "meta.llama2-13b-chat-v1": 2048,
    # "meta.llama2-13b-chat-v1:0:4k": 2048,
    # "meta.llama2-70b-v1": 2048,
    # "meta.llama2-70b-v1:0:4k": 2048,
    # "meta.llama2-70b-chat-v1": 2048,
    # "meta.llama2-70b-chat-v1:0:4k": 2048,
    # Llama 3 Instruct
    # "meta.llama3-8b-instruct-v1:0": 2048,
    "meta.llama3-70b-instruct-v1:0": 2048,
    # Llama 3.1 Instruct
    # "meta.llama3-1-8b-instruct-v1:0": 2048,
    "meta.llama3-1-70b-instruct-v1:0": 2048,
    "meta.llama3-1-405b-instruct-v1:0": 2048,
    # Llama 3.2 Instruct
    # "meta.llama3-2-3b-instruct-v1:0": 2048,
    # "meta.llama3-2-11b-instruct-v1:0": 2048,
    "meta.llama3-2-90b-instruct-v1:0": 2048,
    # Mistral 7B Instruct
    # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-mistral-text-completion.html
    # "mistral.mistral-7b-instruct-v0:2": 8192,
    # Mixtral 8x7B Instruct
    "mistral.mixtral-8x7b-instruct-v0:1": 4096,
    # Mistral Small
    "mistral.mistral-small-2402-v1:0": 8192,
    # Mistral Large (24.02)
    "mistral.mistral-large-2402-v1:0": 8192,
    # Mistral Large 2 (24.07)
    "mistral.mistral-large-2407-v1:0": 8192,
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
        max_tokens = (NOT_SUPPORT_STREAM_MODELS | SUPPORT_STREAM_MODELS)[model_id]
    except KeyError:
        logger.warning(f"Couldn't find model:{model_id} , max tokens has been set to 2048")
        max_tokens = 2048
    return max_tokens
