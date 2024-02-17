from openai.types.chat.chat_completion import (
    ChatCompletion,
    ChatCompletionMessage,
    Choice,
)
import pytest

from openai.types.completion_usage import CompletionUsage
from metagpt.llm import LLM
from metagpt.provider.openai_like_api import OpenAILIKE
from tests.metagpt.provider.mock_llm_config import mock_llm_config_openailike

resp_content = ' 1\n2\n3\n4\n5\n6\n7\n8\n9\n10'
default_resp = ChatCompletion(
    id='cmpl-ae9688c1d46b4ed28f6ef53e06152121',
    choices=[
        Choice(
            finish_reason='stop',
            index=0,
            logprobs=None,
            message=ChatCompletionMessage(content=resp_content, role='assistant', function_call=None, tool_calls=None)
        )
    ],
    created=2777813,
    model='moonshot-v1-8k',
    object='chat.completion',
    system_fingerprint=None,
    usage=CompletionUsage(completion_tokens=21, prompt_tokens=15, total_tokens=36))

hello_msg = [{"role": "user", "content": "count from 1 to 10. split by newline."}]

@pytest.mark.asyncio
async def test_openai_like_acompletion():
    llm = OpenAILIKE(mock_llm_config_openailike)

    resp = await llm.acompletion(hello_msg)
    assert resp.choices[0].message.content == resp_content

    resp = await llm.acompletion_text(hello_msg, stream=False)
    assert resp == resp_content

    resp = await llm.acompletion_text(hello_msg,stream=True)
    assert  resp == resp_content



