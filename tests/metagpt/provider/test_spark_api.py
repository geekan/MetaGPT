"""
用于讯飞星火SDK的测试用例
文档：https://www.xfyun.cn/doc/spark/Web.html
"""


import pytest

from metagpt.provider.spark_api import SparkLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_spark
from tests.metagpt.provider.req_resp_const import (
    llm_general_chat_funcs_test,
    messages,
    prompt,
    resp_cont_tmpl,
)

resp_cont = resp_cont_tmpl.format(name="Spark")


def mock_spark_acreate(self, messages, stream):
    pass


@pytest.mark.asyncio
async def test_spark_acompletion(mocker):
    mocker.patch("metagpt.provider.spark_api.SparkLLM.acreate", mock_spark_acreate)

    spark_llm = SparkLLM(mock_llm_config_spark)

    resp = await spark_llm.acompletion([messages])
    assert resp == resp_cont

    await llm_general_chat_funcs_test(spark_llm, prompt, prompt, resp_cont)
