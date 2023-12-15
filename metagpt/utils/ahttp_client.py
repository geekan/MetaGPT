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
    """
    usage:
        result = astream(url="xx")
        async for line in result:
            deal_with(line)
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, params=params, json=json, data=data, headers=headers, timeout=timeout) as resp:
            async for line in resp.content:
                yield line.decode(encoding)
