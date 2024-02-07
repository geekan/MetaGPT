#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : default request & response data for provider unittest

from openai.types.chat.chat_completion import (
    ChatCompletion,
    ChatCompletionMessage,
    Choice,
)
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as AChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.completion_usage import CompletionUsage

prompt = "who are you?"
messages = [{"role": "user", "content": prompt}]

resp_cont_tmpl = "I'm {name}"
default_resp_cont = resp_cont_tmpl.format(name="GPT")


# part of whole ChatCompletion of openai like structure
def get_part_chat_completion(llm_name: str) -> dict:
    part_chat_completion = {
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": resp_cont_tmpl.format(name=llm_name),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"completion_tokens": 22, "prompt_tokens": 19, "total_tokens": 41},
    }
    return part_chat_completion


def get_openai_chat_completion(llm_name: str) -> ChatCompletion:
    openai_chat_completion = ChatCompletion(
        id="cmpl-a6652c1bb181caae8dd19ad8",
        model="xx/xxx",
        object="chat.completion",
        created=1703300855,
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(role="assistant", content=resp_cont_tmpl.format(name=llm_name)),
                logprobs=None,
            )
        ],
        usage=CompletionUsage(completion_tokens=110, prompt_tokens=92, total_tokens=202),
    )
    return openai_chat_completion


def get_openai_chat_completion_chunk(llm_name: str, usage_as_dict: bool = False) -> ChatCompletionChunk:
    usage = CompletionUsage(completion_tokens=110, prompt_tokens=92, total_tokens=202)
    usage = usage if not usage_as_dict else usage.model_dump()
    openai_chat_completion_chunk = ChatCompletionChunk(
        id="cmpl-a6652c1bb181caae8dd19ad8",
        model="xx/xxx",
        object="chat.completion.chunk",
        created=1703300855,
        choices=[
            AChoice(
                delta=ChoiceDelta(role="assistant", content=resp_cont_tmpl.format(name=llm_name)),
                finish_reason="stop",
                index=0,
                logprobs=None,
            )
        ],
        usage=usage,
    )
    return openai_chat_completion_chunk


gemini_messages = [{"role": "user", "parts": prompt}]
