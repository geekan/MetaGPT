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
    """Parses a single line from a stream, extracting relevant data.

    Args:
        line: A single line from a stream as bytes.

    Returns:
        The processed line as bytes if relevant, None otherwise.
    """
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
    """Parses an iterator of bytes, yielding relevant data lines.

    Args:
        rbody: An iterator of bytes representing the response body.

    Returns:
        An iterator of processed lines as bytes.
    """
    for line in rbody:
        _line = parse_stream_helper(line)
        if _line is not None:
            yield _line


class GeneralAPIRequestor(APIRequestor):
    """Handles API requests, interpreting responses according to the content type.

    This class extends from APIRequestor to provide methods for handling synchronous
    and asynchronous API requests, specifically interpreting responses based on whether
    they are streamed or not.

    Attributes:
        base_url: The base URL for the API.
    """

    def _interpret_response_line(self, rbody: bytes, rcode: int, rheaders, stream: bool) -> bytes:
        """Interprets a single line of the response body.

        Args:
            rbody: The response body as bytes.
            rcode: The response code.
            rheaders: The response headers.
            stream: A boolean indicating if the response is a stream.

        Returns:
            The interpreted response line as bytes.
        """
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
        """Interprets the response from an asynchronous API request.

        Args:
            result: The response object from the aiohttp library.
            stream: A boolean indicating if the response is a stream.

        Returns:
            A tuple containing the interpreted response and a boolean indicating if it is a stream.
        """
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
