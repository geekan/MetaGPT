#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of APIRequestor

import pytest

from metagpt.provider.general_api_requestor import (
    GeneralAPIRequestor,
    parse_stream,
    parse_stream_helper,
)

api_requestor = GeneralAPIRequestor(base_url="http://www.baidu.com")


def test_parse_stream():
    assert parse_stream_helper(None) is None
    assert parse_stream_helper(b"data: [DONE]") is None
    assert parse_stream_helper(b"data: test") == b"test"
    assert parse_stream_helper(b"test") is None
    for line in parse_stream([b"data: test"]):
        assert line == b"test"


def test_api_requestor():
    resp, _, _ = api_requestor.request(method="get", url="/s?wd=baidu")
    assert b"baidu" in resp


@pytest.mark.asyncio
async def test_async_api_requestor():
    resp, _, _ = await api_requestor.arequest(method="get", url="/s?wd=baidu")
    assert b"baidu" in resp
