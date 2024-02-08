#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : General Async API for http-based LLM model

import asyncio
from typing import AsyncGenerator, Generator, Iterator, Tuple, Union

import aiohttp
import requests

from metagpt.logs import logger
from metagpt.provider.general_api_base import APIRequestor


def parse_stream_helper(line: bytes) -> Union[bytes, None]:
    if line and line.startswith(b"data:"):
        if line.startswith(b"data: "):
            # SSE event may be valid when it contain whitespace
            line = line[len(b"data: ") :]
        else:
            line = line[len(b"data:") :]
        if line.strip() == b"[DONE]":
            # return here will cause GeneratorExit exception in urllib3
            # and it will close http connection with TCP Reset
            return None
        else:
            return line
    return None


def parse_stream(rbody: Iterator[bytes]) -> Iterator[bytes]:
    for line in rbody:
        _line = parse_stream_helper(line)
        if _line is not None:
            yield _line


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

    def _interpret_response_line(self, rbody: bytes, rcode: int, rheaders, stream: bool) -> bytes:
        # just do nothing to meet the APIRequestor process and return the raw data
        # due to the openai sdk will convert the data into OpenAIResponse which we don't need in general cases.

        return rbody

    def _interpret_response(
        self, result: requests.Response, stream: bool
    ) -> Tuple[Union[bytes, Iterator[Generator]], bytes]:
        """Returns the response(s) and a bool indicating whether it is a stream."""
        content_type = result.headers.get("Content-Type", "")
        if stream and ("text/event-stream" in content_type or "application/x-ndjson" in content_type):
            return (
                self._interpret_response_line(line, result.status_code, result.headers, stream=True)
                for line in parse_stream(result.iter_lines())
            ), True
        else:
            return (
                self._interpret_response_line(
                    result.content,  # let the caller to decode the msg
                    result.status_code,
                    result.headers,
                    stream=False,
                ),
                False,
            )

    async def _interpret_async_response(
        self, result: aiohttp.ClientResponse, stream: bool
    ) -> Tuple[Union[bytes, AsyncGenerator[bytes, None]], bool]:
        content_type = result.headers.get("Content-Type", "")
        if stream and ("text/event-stream" in content_type or "application/x-ndjson" in content_type):
            # the `Content-Type` of ollama stream resp is "application/x-ndjson"
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
