#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : General Async API for http-based LLM model

import asyncio
from typing import AsyncGenerator, Tuple, Union

import aiohttp

from metagpt.logs import logger
from metagpt.provider.general_api_base import APIRequestor


class GeneralAPIRequestor(APIRequestor):
    """
    usage
        # full_url = "{base_url}{url}"
        requester = GeneralAPIRequestor(base_url=base_url)
        result, _, api_key = await requester.arequest(
            method=method,
            url=url,
            headers=headers,
            stream=stream,
            params=kwargs,
            request_timeout=120
        )
    """

    def _interpret_response_line(self, rbody: str, rcode: int, rheaders, stream: bool) -> str:
        # just do nothing to meet the APIRequestor process and return the raw data
        # due to the openai sdk will convert the data into OpenAIResponse which we don't need in general cases.

        return rbody

    async def _interpret_async_response(
        self, result: aiohttp.ClientResponse, stream: bool
    ) -> Tuple[Union[str, AsyncGenerator[str, None]], bool]:
        if stream and "text/event-stream" in result.headers.get("Content-Type", ""):
            return (
                self._interpret_response_line(line, result.status, result.headers, stream=True)
                async for line in result.content
            ), True
        else:
            try:
                await result.read()
            except (aiohttp.ServerTimeoutError, asyncio.TimeoutError) as e:
                raise TimeoutError("Request timed out") from e
            except aiohttp.ClientError as exp:
                logger.warning(f"response: {result.content}, exp: {exp}")
            return (
                self._interpret_response_line(
                    await result.read(),  # let the caller to decode the msg
                    result.status,
                    result.headers,
                    stream=False,
                ),
                False,
            )
