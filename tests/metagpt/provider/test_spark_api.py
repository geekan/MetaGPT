"""
用于讯飞星火SDK的测试用例
文档：https://www.xfyun.cn/doc/spark/Web.html
"""


from typing import AsyncIterator, List

import pytest
from sparkai.core.messages.ai import AIMessage, AIMessageChunk
from sparkai.core.outputs.chat_generation import ChatGeneration
from sparkai.core.outputs.llm_result import LLMResult

from metagpt.provider.spark_api import SparkLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_spark
from tests.metagpt.provider.req_resp_const import (
    llm_general_chat_funcs_test,
    messages,
    prompt,
    resp_cont_tmpl,
)

resp_cont = resp_cont_tmpl.format(name="Spark")
USAGE = {
    "token_usage": {"question_tokens": 1000, "prompt_tokens": 1000, "completion_tokens": 1000, "total_tokens": 2000}
}
spark_agenerate_result = LLMResult(
    generations=[[ChatGeneration(text=resp_cont, message=AIMessage(content=resp_cont, additional_kwargs=USAGE))]]
)

chunks = [AIMessageChunk(content=resp_cont), AIMessageChunk(content="", additional_kwargs=USAGE)]


async def chunk_iterator(chunks: List[AIMessageChunk]) -> AsyncIterator[AIMessageChunk]:
    for chunk in chunks:
        yield chunk


async def mock_spark_acreate(self, messages, stream):
    if stream:
        return chunk_iterator(chunks)
    else:
        return spark_agenerate_result


@pytest.mark.asyncio
async def test_spark_acompletion(mocker):
    mocker.patch("metagpt.provider.spark_api.SparkLLM.acreate", mock_spark_acreate)

    spark_llm = SparkLLM(mock_llm_config_spark)

    resp = await spark_llm.acompletion([messages])
    assert spark_llm.get_choice_text(resp) == resp_cont

    await llm_general_chat_funcs_test(spark_llm, prompt, messages, resp_cont)
