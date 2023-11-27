#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : zhipu model api to support sync & async for invoke & sse_invoke

import zhipuai
from zhipuai.model_api.api import ModelAPI, InvokeType
from zhipuai.utils.http_client import headers as zhipuai_default_headers

from metagpt.provider.zhipuai.async_sse_client import AsyncSSEClient
from metagpt.provider.general_api_requestor import GeneralAPIRequestor


class ZhiPuModelAPI(ModelAPI):

    @classmethod
    def get_header(cls) -> dict:
        token = cls._generate_token()
        zhipuai_default_headers.update({"Authorization": token})
        return zhipuai_default_headers

    @classmethod
    def get_sse_header(cls) -> dict:
        token = cls._generate_token()
        headers = {
            "Authorization": token
        }
        return headers

    @classmethod
    def split_zhipu_api_url(cls, invoke_type: InvokeType, kwargs):
        # use this method to prevent zhipu api upgrading to different version.
        # and follow the GeneralAPIRequestor implemented based on openai sdk
        zhipu_api_url = cls._build_api_url(kwargs, invoke_type)
        """
            example:
                zhipu_api_url: https://open.bigmodel.cn/api/paas/v3/model-api/{model}/{invoke_method}
        """
        arr = zhipu_api_url.split("/api/")
        # ("https://open.bigmodel.cn/api/" , "/paas/v3/model-api/chatglm_turbo/invoke")
        return f"{arr[0]}/api", f"/{arr[1]}"

    @classmethod
    async def arequest(cls, invoke_type: InvokeType, stream: bool, method: str, headers: dict, kwargs):
        # TODO to make the async request to be more generic for models in http mode.
        assert method in ["post", "get"]

        api_base, url = cls.split_zhipu_api_url(invoke_type, kwargs)
        requester = GeneralAPIRequestor(api_base=api_base)
        result, _, api_key = await requester.arequest(
            method=method,
            url=url,
            headers=headers,
            stream=stream,
            params=kwargs,
            request_timeout=zhipuai.api_timeout_seconds
        )

        return result

    @classmethod
    async def ainvoke(cls, **kwargs) -> dict:
        """ async invoke different from raw method `async_invoke` which get the final result by task_id"""
        headers = cls.get_header()
        resp = await cls.arequest(invoke_type=InvokeType.SYNC,
                                  stream=False,
                                  method="post",
                                  headers=headers,
                                  kwargs=kwargs)
        return resp

    @classmethod
    async def asse_invoke(cls, **kwargs) -> AsyncSSEClient:
        """ async sse_invoke """
        headers = cls.get_sse_header()
        return AsyncSSEClient(await cls.arequest(invoke_type=InvokeType.SSE,
                                                 stream=True,
                                                 method="post",
                                                 headers=headers,
                                                 kwargs=kwargs))
