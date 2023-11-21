#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : General Async API for http-based LLM model

from typing import AsyncGenerator, Tuple, Union, Optional, Literal
import aiohttp
import asyncio

from openai.api_requestor import APIRequestor

from metagpt.logs import logger


class GeneralAPIRequestor(APIRequestor):
    """
    usage
        # full_url = "{api_base}{url}"
        requester = GeneralAPIRequestor(api_base=api_base)
        result, _, api_key = await requester.arequest(
            method=method,
            url=url,
            headers=headers,
            stream=stream,
            params=kwargs,
            request_timeout=120
        )
    """

    def _interpret_response_line(
        self, rbody: str, rcode: int, rheaders, stream: bool
    ) -> str:
        # just do nothing to meet the APIRequestor process and return the raw data
        # due to the openai sdk will convert the data into OpenAIResponse which we don't need in general cases.

        return rbody

    async def _interpret_async_response(
        self, result: aiohttp.ClientResponse, stream: bool
    ) -> Tuple[Union[str, AsyncGenerator[str, None]], bool]:
        if stream and "text/event-stream" in result.headers.get("Content-Type", ""):
            return (
                   self._interpret_response_line(
                       line, result.status, result.headers, stream=True
                   )
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
