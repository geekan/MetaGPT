#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : zhipu model api to support sync & async for invoke & sse_invoke

import json

from zhipuai import ZhipuAI
from zhipuai.core._http_client import ZHIPUAI_DEFAULT_TIMEOUT

from metagpt.provider.general_api_requestor import GeneralAPIRequestor
from metagpt.provider.zhipuai.async_sse_client import AsyncSSEClient


class ZhiPuModelAPI(ZhipuAI):
    def split_zhipu_api_url(self):
        # use this method to prevent zhipu api upgrading to different version.
        # and follow the GeneralAPIRequestor implemented based on openai sdk
        zhipu_api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        arr = zhipu_api_url.split("/api/")
        # ("https://open.bigmodel.cn/api" , "/paas/v4/chat/completions")
        return f"{arr[0]}/api", f"/{arr[1]}"

    async def arequest(self, stream: bool, method: str, headers: dict, kwargs):
        # TODO to make the async request to be more generic for models in http mode.
        assert method in ["post", "get"]

        base_url, url = self.split_zhipu_api_url()
        requester = GeneralAPIRequestor(base_url=base_url)
        result, _, api_key = await requester.arequest(
            method=method,
            url=url,
            headers=headers,
            stream=stream,
            params=kwargs,
            request_timeout=ZHIPUAI_DEFAULT_TIMEOUT.read,
        )
        return result

    async def acreate(self, **kwargs) -> dict:
        """async invoke different from raw method `async_invoke` which get the final result by task_id"""
        headers = self._default_headers
        resp = await self.arequest(stream=False, method="post", headers=headers, kwargs=kwargs)
        resp = resp.decode("utf-8")
        resp = json.loads(resp)
        if "error" in resp:
            raise RuntimeError(
                f"Request failed, msg: {resp}, please ref to `https://open.bigmodel.cn/dev/api#error-code-v3`"
            )
        return resp

    async def acreate_stream(self, **kwargs) -> AsyncSSEClient:
        """async sse_invoke"""
        headers = self._default_headers
        return AsyncSSEClient(await self.arequest(stream=True, method="post", headers=headers, kwargs=kwargs))
