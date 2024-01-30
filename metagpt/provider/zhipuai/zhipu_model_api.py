#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : zhipu model api to support sync & async for invoke & sse_invoke

import json

from zhipuai import ZhipuAI
from zhipuai.core._http_client import ZHIPUAI_DEFAULT_TIMEOUT

from metagpt.provider.general_api_requestor import GeneralAPIRequestor
from metagpt.provider.zhipuai.async_sse_client import AsyncSSEClient


class ZhiPuModelAPI(ZhipuAI):
    """API wrapper for ZhiPu Model.

    This class provides methods to interact with ZhiPu Model API.
    """

    def split_zhipu_api_url(self):
        """Splits the ZhiPu API URL into base URL and endpoint.

        Returns:
            A tuple containing the base URL and the endpoint.
        """
        # use this method to prevent zhipu api upgrading to different version.
        # and follow the GeneralAPIRequestor implemented based on openai sdk
        zhipu_api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        arr = zhipu_api_url.split("/api/")
        # ("https://open.bigmodel.cn/api" , "/paas/v4/chat/completions")
        return f"{arr[0]}/api", f"/{arr[1]}"

    async def arequest(self, stream: bool, method: str, headers: dict, kwargs):
        """Asynchronously sends a request to the ZhiPu API.

        Args:
            stream: Whether to stream the response.
            method: The HTTP method to use ('post' or 'get').
            headers: The headers to send with the request.
            kwargs: Additional keyword arguments to send with the request.

        Returns:
            The result of the API request.
        """
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
        """Asynchronously invokes the ZhiPu API and returns the result.

        This method differs from `async_invoke` by directly returning the result without using a task ID.

        Args:
            **kwargs: Keyword arguments to send with the request.

        Returns:
            A dictionary containing the response from the API.

        Raises:
            RuntimeError: If the request fails.
        """
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
        """Asynchronously invokes the ZhiPu API and returns a streaming client.

        Args:
            **kwargs: Keyword arguments to send with the request.

        Returns:
            An instance of AsyncSSEClient for streaming responses.
        """
        headers = self._default_headers
        return AsyncSSEClient(await self.arequest(stream=True, method="post", headers=headers, kwargs=kwargs))
