#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : 

import pytest
import os
import requests
import aiohttp
from typing import Iterator, Tuple, Union, Generator, AsyncGenerator

from openai import OpenAIError
from metagpt.provider.general_api_base import ApiType, log_debug, log_info, log_warn, OpenAIResponse, \
    _requests_proxies_arg, _aiohttp_proxies_arg, _make_session, parse_stream_helper, parse_stream, APIRequestor


def test_basic():
    _ = ApiType.from_str("azure")
    _ = ApiType.from_str("azuread")
    _ = ApiType.from_str("openai")
    with pytest.raises(OpenAIError):
        _ = ApiType.from_str("xx")

    os.environ.setdefault("LLM_LOG", "debug")
    log_debug("debug")
    log_warn("warn")
    log_info("info")


def test_openai_response():
    resp = OpenAIResponse(data=[], headers={"retry-after": 3})
    assert resp.request_id is None
    assert resp.retry_after == 3
    assert resp.operation_location is None
    assert resp.organization is None
    assert resp.response_ms is None


def test_proxy():
    assert _requests_proxies_arg(proxy=None) is None

    proxy = "127.0.0.1:80"
    assert _requests_proxies_arg(proxy=proxy) == {"http": proxy, "https": proxy}
    proxy_dict = {"http": proxy}
    assert _requests_proxies_arg(proxy=proxy_dict) == proxy_dict
    proxy_dict = {"https": proxy}
    assert _requests_proxies_arg(proxy=proxy_dict) == proxy_dict

    assert _make_session() is not None


def test_parse_stream():
    assert parse_stream_helper(None) is None
    assert parse_stream_helper(b"data: [DONE]") is None
    assert parse_stream_helper(b"data: test") == "test"
    assert parse_stream_helper(b"test") is None
    for line in parse_stream([b"data: test"]):
        assert line == "test"


api_requestor = APIRequestor(base_url="http://www.baidu.com")


def mock_interpret_response(self, result: requests.Response, stream: bool
    ) -> Tuple[Union[bytes, Iterator[Generator]], bytes]:
    return b"baidu", False


async def mock_interpret_async_response(self, result: aiohttp.ClientResponse, stream: bool
    ) -> Tuple[Union[OpenAIResponse, AsyncGenerator[OpenAIResponse, None]], bool]:
    return b"baidu", True


def test_api_requestor(mocker):
    mocker.patch("metagpt.provider.general_api_base.APIRequestor._interpret_response", mock_interpret_response)
    resp, _, _ = api_requestor.request(method="get", url="/s?wd=baidu")

    resp, _, _ = api_requestor.request(method="post", url="/s?wd=baidu")


@pytest.mark.asyncio
async def test_async_api_requestor(mocker):
    mocker.patch("metagpt.provider.general_api_base.APIRequestor._interpret_async_response", mock_interpret_async_response)
    resp, _, _ = await api_requestor.arequest(method="get", url="/s?wd=baidu")
    resp, _, _ = await api_requestor.arequest(method="post", url="/s?wd=baidu")
