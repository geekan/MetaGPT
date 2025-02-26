#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : General Async API for http-based LLM model

import asyncio
from typing import AsyncGenerator, Iterator, Optional, Tuple, Union

import aiohttp
import requests

from metagpt.logs import logger
from metagpt.provider.general_api_base import APIRequestor, OpenAIResponse


def parse_stream_helper(line: bytes) -> Optional[bytes]:
    if line and line.startswith(b"data:"):
        if line.startswith(b"data: "):
            # SSE event may be valid when it contains whitespace
            line = line[len(b"data: ") :]
        else:
            line = line[len(b"data:") :]
        if line.strip() == b"[DONE]":
            # Returning None to indicate end of stream
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
    Usage example:
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

    def _interpret_response_line(self, rbody: bytes, rcode: int, rheaders: dict, stream: bool) -> OpenAIResponse:
        """
        Process and return the response data wrapped in OpenAIResponse.

        Args:
            rbody (bytes): The response body.
            rcode (int): The response status code.
            rheaders (dict): The response headers.
            stream (bool): Whether the response is a stream.

        Returns:
            OpenAIResponse: The response data wrapped in OpenAIResponse.
        """
        return OpenAIResponse(rbody, rheaders)

    def _interpret_response(
        self, result: requests.Response, stream: bool
    ) -> Tuple[Union[OpenAIResponse, Iterator[OpenAIResponse]], bool]:
        """
        Interpret a synchronous response.

        Args:
            result (requests.Response): The response object.
            stream (bool): Whether the response is a stream.

        Returns:
            Tuple[Union[OpenAIResponse, Iterator[OpenAIResponse]], bool]: A tuple containing the response content and a boolean indicating if it is a stream.
        """
        content_type = result.headers.get("Content-Type", "")
        if stream and ("text/event-stream" in content_type or "application/x-ndjson" in content_type):
            return (
                (
                    self._interpret_response_line(line, result.status_code, result.headers, stream=True)
                    for line in parse_stream(result.iter_lines())
                ),
                True,
            )
        else:
            return (
                self._interpret_response_line(
                    result.content,  # let the caller decode the msg
                    result.status_code,
                    result.headers,
                    stream=False,
                ),
                False,
            )

    async def _interpret_async_response(
        self, result: aiohttp.ClientResponse, stream: bool
    ) -> Tuple[Union[OpenAIResponse, AsyncGenerator[OpenAIResponse, None]], bool]:
        """
        Interpret an asynchronous response.

        Args:
            result (aiohttp.ClientResponse): The response object.
            stream (bool): Whether the response is a stream.

        Returns:
            Tuple[Union[OpenAIResponse, AsyncGenerator[OpenAIResponse, None]], bool]: A tuple containing the response content and a boolean indicating if it is a stream.
        """
        content_type = result.headers.get("Content-Type", "")
        if stream and (
            "text/event-stream" in content_type or "application/x-ndjson" in content_type or content_type == ""
        ):
            return (
                (
                    self._interpret_response_line(line, result.status, result.headers, stream=True)
                    async for line in result.content
                ),
                True,
            )
        else:
            try:
                response_content = await result.read()
            except (aiohttp.ServerTimeoutError, asyncio.TimeoutError) as e:
                raise TimeoutError("Request timed out") from e
            except aiohttp.ClientError as exp:
                logger.warning(f"response: {result}, exp: {exp}")
                response_content = b""
            return (
                self._interpret_response_line(
                    response_content,  # let the caller decode the msg
                    result.status,
                    result.headers,
                    stream=False,
                ),
                False,
            )
