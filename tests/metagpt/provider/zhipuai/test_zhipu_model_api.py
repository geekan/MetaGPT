#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from typing import Any, Tuple

import pytest
import zhipuai
from zhipuai.model_api.api import InvokeType
from zhipuai.utils.http_client import headers as zhipuai_default_headers

from metagpt.provider.zhipuai.zhipu_model_api import ZhiPuModelAPI

api_key = "xxx.xxx"
zhipuai.api_key = api_key

default_resp = b'{"result": "test response"}'


async def mock_requestor_arequest(self, **kwargs) -> Tuple[Any, Any, str]:
    return default_resp, None, None


@pytest.mark.asyncio
async def test_zhipu_model_api(mocker):
    header = ZhiPuModelAPI.get_header()
    zhipuai_default_headers.update({"Authorization": api_key})
    assert header == zhipuai_default_headers

    sse_header = ZhiPuModelAPI.get_sse_header()
    assert len(sse_header["Authorization"]) == 191

    url_prefix, url_suffix = ZhiPuModelAPI.split_zhipu_api_url(InvokeType.SYNC, kwargs={"model": "chatglm_turbo"})
    assert url_prefix == "https://open.bigmodel.cn/api"
    assert url_suffix == "/paas/v3/model-api/chatglm_turbo/invoke"

    mocker.patch("metagpt.provider.general_api_requestor.GeneralAPIRequestor.arequest", mock_requestor_arequest)
    result = await ZhiPuModelAPI.arequest(
        InvokeType.SYNC, stream=False, method="get", headers={}, kwargs={"model": "chatglm_turbo"}
    )
    assert result == default_resp

    result = await ZhiPuModelAPI.ainvoke()
    assert result["result"] == "test response"
