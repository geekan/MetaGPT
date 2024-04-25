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

