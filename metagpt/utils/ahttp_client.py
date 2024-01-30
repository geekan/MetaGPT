#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : pure async http_client

from typing import Any, Mapping, Optional, Union

import aiohttp
from aiohttp.client import DEFAULT_TIMEOUT


async def apost(
    url: str,
    params: Optional[Mapping[str, str]] = None,
    json: Any = None,
    data: Any = None,
    headers: Optional[dict] = None,
    as_json: bool = False,
    encoding: str = "utf-8",
    timeout: int = DEFAULT_TIMEOUT.total,
) -> Union[str, dict]:
    """Asynchronously posts data to a specified URL and returns the response.

    This function supports sending both JSON and form data and can return the response as either a JSON object or a plain text string.

    Args:
        url: The URL to send the request to.
        params: Optional dictionary of URL parameters.
        json: JSON data to send in the body of the request.
        data: Form data to send in the body of the request.
        headers: Optional dictionary of request headers.
        as_json: If True, returns the response as a JSON object. Otherwise, returns a plain text string.
        encoding: The encoding to use for decoding the response.
        timeout: The timeout for the request in seconds.

    Returns:
        The response from the server, either as a dictionary if `as_json` is True, or as a string.
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, params=params, json=json, data=data, headers=headers, timeout=timeout) as resp:
            if as_json:
                data = await resp.json()
            else:
                data = await resp.read()
                data = data.decode(encoding)
    return data


async def apost_stream(
    url: str,
    params: Optional[Mapping[str, str]] = None,
    json: Any = None,
    data: Any = None,
    headers: Optional[dict] = None,
    encoding: str = "utf-8",
    timeout: int = DEFAULT_TIMEOUT.total,
) -> Any:
    """Asynchronously posts data to a specified URL and yields the response line by line.

    This function is useful for streaming responses from the server. It supports sending both JSON and form data.

    Usage example:
        result = apost_stream(url="http://example.com")
        async for line in result:
            process(line)

    Args:
        url: The URL to send the request to.
        params: Optional dictionary of URL parameters.
        json: JSON data to send in the body of the request.
        data: Form data to send in the body of the request.
        headers: Optional dictionary of request headers.
        encoding: The encoding to use for decoding the response lines.
        timeout: The timeout for the request in seconds.

    Yields:
        Each line of the response, decoded using the specified encoding.

    """
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, params=params, json=json, data=data, headers=headers, timeout=timeout) as resp:
            async for line in resp.content:
                yield line.decode(encoding)
