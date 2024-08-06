#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : default request & response data for provider unittest


from anthropic.types import (
    ContentBlock,
    ContentBlockDeltaEvent,
    Message,
    MessageStartEvent,
    TextDelta,
)
from anthropic.types import Usage as AnthropicUsage
from dashscope.api_entities.dashscope_response import (
    DashScopeAPIResponse,
    GenerationOutput,
    GenerationResponse,
    GenerationUsage,
)
from openai.types.chat.chat_completion import (
    ChatCompletion,
    ChatCompletionMessage,
    Choice,
)
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as AChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.completion_usage import CompletionUsage
from qianfan.resources.typing import QfResponse

from metagpt.provider.base_llm import BaseLLM

prompt = "who are you?"
messages = [{"role": "user", "content": prompt}]

resp_cont_tmpl = "I'm {name}"
default_resp_cont = resp_cont_tmpl.format(name="GPT")


# part of whole ChatCompletion of openai like structure
def get_part_chat_completion(name: str) -> dict:
    part_chat_completion = {
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": resp_cont_tmpl.format(name=name),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"completion_tokens": 22, "prompt_tokens": 19, "total_tokens": 41},
    }
    return part_chat_completion


def get_openai_chat_completion(name: str) -> ChatCompletion:
    openai_chat_completion = ChatCompletion(
        id="cmpl-a6652c1bb181caae8dd19ad8",
        model="xx/xxx",
        object="chat.completion",
        created=1703300855,
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(role="assistant", content=resp_cont_tmpl.format(name=name)),
                logprobs=None,
            )
        ],
        usage=CompletionUsage(completion_tokens=110, prompt_tokens=92, total_tokens=202),
    )
    return openai_chat_completion


def get_openai_chat_completion_chunk(name: str, usage_as_dict: bool = False) -> ChatCompletionChunk:
    usage = CompletionUsage(completion_tokens=110, prompt_tokens=92, total_tokens=202)
    usage = usage if not usage_as_dict else usage.model_dump()
    openai_chat_completion_chunk = ChatCompletionChunk(
        id="cmpl-a6652c1bb181caae8dd19ad8",
        model="xx/xxx",
        object="chat.completion.chunk",
        created=1703300855,
        choices=[
            AChoice(
                delta=ChoiceDelta(role="assistant", content=resp_cont_tmpl.format(name=name)),
                finish_reason="stop",
                index=0,
                logprobs=None,
            )
        ],
        usage=usage,
    )
    return openai_chat_completion_chunk


# For gemini
gemini_messages = [{"role": "user", "parts": prompt}]


# For QianFan
qf_jsonbody_dict = {
    "id": "as-4v1h587fyv",
    "object": "chat.completion",
    "created": 1695021339,
    "result": "",
    "is_truncated": False,
    "need_clear_history": False,
    "usage": {"prompt_tokens": 7, "completion_tokens": 15, "total_tokens": 22},
}


def get_qianfan_response(name: str) -> QfResponse:
    qf_jsonbody_dict["result"] = resp_cont_tmpl.format(name=name)
    return QfResponse(code=200, body=qf_jsonbody_dict)


# For DashScope
def get_dashscope_response(name: str) -> GenerationResponse:
    return GenerationResponse.from_api_response(
        DashScopeAPIResponse(
            status_code=200,
            output=GenerationOutput(
                **{
                    "text": "",
                    "finish_reason": "",
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"role": "assistant", "content": resp_cont_tmpl.format(name=name)},
                        }
                    ],
                }
            ),
            usage=GenerationUsage(**{"input_tokens": 12, "output_tokens": 98, "total_tokens": 110}),
        )
    )


# For Anthropic
def get_anthropic_response(name: str, stream: bool = False) -> Message:
    if stream:
        return [
            MessageStartEvent(
                message=Message(
                    id="xxx",
                    model=name,
                    role="assistant",
                    type="message",
                    content=[ContentBlock(text="", type="text")],
                    usage=AnthropicUsage(input_tokens=10, output_tokens=10),
                ),
                type="message_start",
            ),
            ContentBlockDeltaEvent(
                index=0,
                delta=TextDelta(text=resp_cont_tmpl.format(name=name), type="text_delta"),
                type="content_block_delta",
            ),
        ]
    else:
        return Message(
            id="xxx",
            model=name,
            role="assistant",
            type="message",
            content=[ContentBlock(text=resp_cont_tmpl.format(name=name), type="text")],
            usage=AnthropicUsage(input_tokens=10, output_tokens=10),
        )


# For llm general chat functions call
async def llm_general_chat_funcs_test(llm: BaseLLM, prompt: str, messages: list[dict], resp_cont: str):
    resp = await llm.aask(prompt, stream=False)
    assert resp == resp_cont

    resp = await llm.aask(prompt)
    assert resp == resp_cont

    resp = await llm.acompletion_text(messages, stream=False)
    assert resp == resp_cont

    resp = await llm.acompletion_text(messages, stream=True)
    assert resp == resp_cont


# For Amazon Bedrock
# Check the API documentation of each model
# https://docs.aws.amazon.com/bedrock/latest/userguide
BEDROCK_PROVIDER_REQUEST_BODY = {
    "mistral": {"prompt": "", "max_tokens": 0, "stop": [], "temperature": 0.0, "top_p": 0.0, "top_k": 0},
    "meta": {"prompt": "", "temperature": 0.0, "top_p": 0.0, "max_gen_len": 0},
    "ai21": {
        "prompt": "",
        "temperature": 0.0,
        "topP": 0.0,
        "maxTokens": 0,
        "stopSequences": [],
        "countPenalty": {"scale": 0.0},
        "presencePenalty": {"scale": 0.0},
        "frequencyPenalty": {"scale": 0.0},
    },
    "cohere": {
        "prompt": "",
        "temperature": 0.0,
        "p": 0.0,
        "k": 0.0,
        "max_tokens": 0,
        "stop_sequences": [],
        "return_likelihoods": "NONE",
        "stream": False,
        "num_generations": 0,
        "logit_bias": {},
        "truncate": "NONE",
    },
    "anthropic": {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 0,
        "system": "",
        "messages": [{"role": "", "content": ""}],
        "temperature": 0.0,
        "top_p": 0.0,
        "top_k": 0,
        "stop_sequences": [],
    },
    "amazon": {
        "inputText": "",
        "textGenerationConfig": {"temperature": 0.0, "topP": 0.0, "maxTokenCount": 0, "stopSequences": []},
    },
}

BEDROCK_PROVIDER_RESPONSE_BODY = {
    "mistral": {"outputs": [{"text": "Hello World", "stop_reason": ""}]},
    "meta": {"generation": "Hello World", "prompt_token_count": 0, "generation_token_count": 0, "stop_reason": ""},
    "ai21": {
        "id": "",
        "prompt": {"text": "Hello World", "tokens": []},
        "completions": [
            {"data": {"text": "Hello World", "tokens": []}, "finishReason": {"reason": "length", "length": 2}}
        ],
    },
    "cohere": {
        "generations": [
            {
                "finish_reason": "",
                "id": "",
                "text": "Hello World",
                "likelihood": 0.0,
                "token_likelihoods": [{"token": 0.0}],
                "is_finished": True,
                "index": 0,
            }
        ],
        "id": "",
        "prompt": "",
    },
    "anthropic": {
        "id": "",
        "model": "",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Hello World"}],
        "stop_reason": "",
        "stop_sequence": "",
        "usage": {"input_tokens": 0, "output_tokens": 0},
    },
    "amazon": {
        "inputTextTokenCount": 0,
        "results": [{"tokenCount": 0, "outputText": "Hello World", "completionReason": ""}],
    },
}
