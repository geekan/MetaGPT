#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : refs to openai 0.x sdk

import asyncio
import json
import os
import platform
import re
import sys
import threading
import time
from contextlib import asynccontextmanager
from enum import Enum
from typing import (
    AsyncGenerator,
    AsyncIterator,
    Dict,
    Iterator,
    Optional,
    Tuple,
    Union,
    overload,
)
from urllib.parse import urlencode, urlsplit, urlunsplit

import aiohttp
import requests

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

import logging

import openai
from openai import version

logger = logging.getLogger("openai")

TIMEOUT_SECS = 600
MAX_SESSION_LIFETIME_SECS = 180
MAX_CONNECTION_RETRIES = 2

# Has one attribute per thread, 'session'.
_thread_context = threading.local()

LLM_LOG = os.environ.get("LLM_LOG", "debug")


class ApiType(Enum):
    AZURE = 1
    OPEN_AI = 2
    AZURE_AD = 3

    @staticmethod
    def from_str(label):
        if label.lower() == "azure":
            return ApiType.AZURE
        elif label.lower() in ("azure_ad", "azuread"):
            return ApiType.AZURE_AD
        elif label.lower() in ("open_ai", "openai"):
            return ApiType.OPEN_AI
        else:
            raise openai.OpenAIError(
                "The API type provided in invalid. Please select one of the supported API types: 'azure', 'azure_ad', 'open_ai'"
            )


api_key_to_header = (
    lambda api, key: {"Authorization": f"Bearer {key}"}
    if api in (ApiType.OPEN_AI, ApiType.AZURE_AD)
    else {"api-key": f"{key}"}
)


def _console_log_level():
    if LLM_LOG in ["debug", "info"]:
        return LLM_LOG
    else:
        return None


def log_debug(message, **params):
    msg = logfmt(dict(message=message, **params))
    if _console_log_level() == "debug":
        print(msg, file=sys.stderr)
    logger.debug(msg)


def log_info(message, **params):
    msg = logfmt(dict(message=message, **params))
    if _console_log_level() in ["debug", "info"]:
        print(msg, file=sys.stderr)
    logger.info(msg)


def log_warn(message, **params):
    msg = logfmt(dict(message=message, **params))
    print(msg, file=sys.stderr)
    logger.warning(msg)


def logfmt(props):
    def fmt(key, val):
        # Handle case where val is a bytes or bytesarray
        if hasattr(val, "decode"):
            val = val.decode("utf-8")
        # Check if val is already a string to avoid re-encoding into ascii.
        if not isinstance(val, str):
            val = str(val)
        if re.search(r"\s", val):
            val = repr(val)
        # key should already be a string
        if re.search(r"\s", key):
            key = repr(key)
        return "{key}={val}".format(key=key, val=val)

    return " ".join([fmt(key, val) for key, val in sorted(props.items())])


class OpenAIResponse:
    def __init__(self, data, headers):
        self._headers = headers
        self.data = data

    @property
    def request_id(self) -> Optional[str]:
        return self._headers.get("request-id")

    @property
    def retry_after(self) -> Optional[int]:
        try:
            return int(self._headers.get("retry-after"))
        except TypeError:
            return None

    @property
    def operation_location(self) -> Optional[str]:
        return self._headers.get("operation-location")

    @property
    def organization(self) -> Optional[str]:
        return self._headers.get("LLM-Organization")

    @property
    def response_ms(self) -> Optional[int]:
        h = self._headers.get("Openai-Processing-Ms")
        return None if h is None else round(float(h))


def _build_api_url(url, query):
    scheme, netloc, path, base_query, fragment = urlsplit(url)

    if base_query:
        query = "%s&%s" % (base_query, query)

    return urlunsplit((scheme, netloc, path, query, fragment))


def _requests_proxies_arg(proxy) -> Optional[Dict[str, str]]:
    """Returns a value suitable for the 'proxies' argument to 'requests.request."""
    if proxy is None:
        return None
    elif isinstance(proxy, str):
        return {"http": proxy, "https": proxy}
    elif isinstance(proxy, dict):
        return proxy.copy()
    else:
        raise ValueError(
            "'openai.proxy' must be specified as either a string URL or a dict with string URL under the https and/or http keys."
        )


def _aiohttp_proxies_arg(proxy) -> Optional[str]:
    """Returns a value suitable for the 'proxies' argument to 'aiohttp.ClientSession.request."""
    if proxy is None:
        return None
    elif isinstance(proxy, str):
        return proxy
    elif isinstance(proxy, dict):
        return proxy["https"] if "https" in proxy else proxy["http"]
    else:
        raise ValueError(
            "'openai.proxy' must be specified as either a string URL or a dict with string URL under the https and/or http keys."
        )


def _make_session() -> requests.Session:
    s = requests.Session()
    s.mount(
        "https://",
        requests.adapters.HTTPAdapter(max_retries=MAX_CONNECTION_RETRIES),
    )
    return s


def parse_stream_helper(line: bytes) -> Optional[str]:
    if line:
        if line.strip() == b"data: [DONE]":
            # return here will cause GeneratorExit exception in urllib3
            # and it will close http connection with TCP Reset
            return None
        if line.startswith(b"data: "):
            line = line[len(b"data: ") :]
            return line.decode("utf-8")
        else:
            return None
    return None


def parse_stream(rbody: Iterator[bytes]) -> Iterator[str]:
    for line in rbody:
        _line = parse_stream_helper(line)
        if _line is not None:
            yield _line


async def parse_stream_async(rbody: aiohttp.StreamReader):
    async for line in rbody:
        _line = parse_stream_helper(line)
        if _line is not None:
            yield _line


class APIRequestor:
    def __init__(
        self,
        key=None,
        base_url=None,
        api_type=None,
        api_version=None,
        organization=None,
    ):
        self.base_url = base_url or openai.base_url
        self.api_key = key or openai.api_key
        self.api_type = ApiType.from_str(api_type) if api_type else ApiType.from_str("openai")
        self.api_version = api_version or openai.api_version
        self.organization = organization or openai.organization

    @overload
    def request(
        self,
        method,
        url,
        params,
        headers,
        files,
        stream: Literal[True],
        request_id: Optional[str] = ...,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = ...,
    ) -> Tuple[Iterator[OpenAIResponse], bool, str]:
        pass

    @overload
    def request(
        self,
        method,
        url,
        params=...,
        headers=...,
        files=...,
        *,
        stream: Literal[True],
        request_id: Optional[str] = ...,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = ...,
    ) -> Tuple[Iterator[OpenAIResponse], bool, str]:
        pass

    @overload
    def request(
        self,
        method,
        url,
        params=...,
        headers=...,
        files=...,
        stream: Literal[False] = ...,
        request_id: Optional[str] = ...,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = ...,
    ) -> Tuple[OpenAIResponse, bool, str]:
        pass

    @overload
    def request(
        self,
        method,
        url,
        params=...,
        headers=...,
        files=...,
        stream: bool = ...,
        request_id: Optional[str] = ...,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = ...,
    ) -> Tuple[Union[OpenAIResponse, Iterator[OpenAIResponse]], bool, str]:
        pass

    def request(
        self,
        method,
        url,
        params=None,
        headers=None,
        files=None,
        stream: bool = False,
        request_id: Optional[str] = None,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> Tuple[Union[OpenAIResponse, Iterator[OpenAIResponse]], bool, str]:
        result = self.request_raw(
            method.lower(),
            url,
            params=params,
            supplied_headers=headers,
            files=files,
            stream=stream,
            request_id=request_id,
            request_timeout=request_timeout,
        )
        resp, got_stream = self._interpret_response(result, stream)
        return resp, got_stream, self.api_key

    @overload
    async def arequest(
        self,
        method,
        url,
        params,
        headers,
        files,
        stream: Literal[True],
        request_id: Optional[str] = ...,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = ...,
    ) -> Tuple[AsyncGenerator[OpenAIResponse, None], bool, str]:
        pass

    @overload
    async def arequest(
        self,
        method,
        url,
        params=...,
        headers=...,
        files=...,
        *,
        stream: Literal[True],
        request_id: Optional[str] = ...,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = ...,
    ) -> Tuple[AsyncGenerator[OpenAIResponse, None], bool, str]:
        pass

    @overload
    async def arequest(
        self,
        method,
        url,
        params=...,
        headers=...,
        files=...,
        stream: Literal[False] = ...,
        request_id: Optional[str] = ...,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = ...,
    ) -> Tuple[OpenAIResponse, bool, str]:
        pass

    @overload
    async def arequest(
        self,
        method,
        url,
        params=...,
        headers=...,
        files=...,
        stream: bool = ...,
        request_id: Optional[str] = ...,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = ...,
    ) -> Tuple[Union[OpenAIResponse, AsyncGenerator[OpenAIResponse, None]], bool, str]:
        pass

    async def arequest(
        self,
        method,
        url,
        params=None,
        headers=None,
        files=None,
        stream: bool = False,
        request_id: Optional[str] = None,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> Tuple[Union[OpenAIResponse, AsyncGenerator[OpenAIResponse, None]], bool, str]:
        ctx = aiohttp_session()
        session = await ctx.__aenter__()
        try:
            result = await self.arequest_raw(
                method.lower(),
                url,
                session,
                params=params,
                supplied_headers=headers,
                files=files,
                request_id=request_id,
                request_timeout=request_timeout,
            )
            resp, got_stream = await self._interpret_async_response(result, stream)
        except Exception:
            await ctx.__aexit__(None, None, None)
            raise
        if got_stream:

            async def wrap_resp():
                assert isinstance(resp, AsyncGenerator)
                try:
                    async for r in resp:
                        yield r
                finally:
                    await ctx.__aexit__(None, None, None)

            return wrap_resp(), got_stream, self.api_key
        else:
            await ctx.__aexit__(None, None, None)
            return resp, got_stream, self.api_key

    def request_headers(self, method: str, extra, request_id: Optional[str]) -> Dict[str, str]:
        user_agent = "LLM/v1 PythonBindings/%s" % (version.VERSION,)

        uname_without_node = " ".join(v for k, v in platform.uname()._asdict().items() if k != "node")
        ua = {
            "bindings_version": version.VERSION,
            "httplib": "requests",
            "lang": "python",
            "lang_version": platform.python_version(),
            "platform": platform.platform(),
            "publisher": "openai",
            "uname": uname_without_node,
        }

        headers = {
            "X-LLM-Client-User-Agent": json.dumps(ua),
            "User-Agent": user_agent,
        }

        headers.update(api_key_to_header(self.api_type, self.api_key))

        if self.organization:
            headers["LLM-Organization"] = self.organization

        if self.api_version is not None and self.api_type == ApiType.OPEN_AI:
            headers["LLM-Version"] = self.api_version
        if request_id is not None:
            headers["X-Request-Id"] = request_id
        headers.update(extra)

        return headers

    def _validate_headers(self, supplied_headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if supplied_headers is None:
            return headers

        if not isinstance(supplied_headers, dict):
            raise TypeError("Headers must be a dictionary")

        for k, v in supplied_headers.items():
            if not isinstance(k, str):
                raise TypeError("Header keys must be strings")
            if not isinstance(v, str):
                raise TypeError("Header values must be strings")
            headers[k] = v

        # NOTE: It is possible to do more validation of the headers, but a request could always
        # be made to the API manually with invalid headers, so we need to handle them server side.

        return headers

    def _prepare_request_raw(
        self,
        url,
        supplied_headers,
        method,
        params,
        files,
        request_id: Optional[str],
    ) -> Tuple[str, Dict[str, str], Optional[bytes]]:
        abs_url = "%s%s" % (self.base_url, url)
        headers = self._validate_headers(supplied_headers)

        data = None
        if method == "get" or method == "delete":
            if params:
                encoded_params = urlencode([(k, v) for k, v in params.items() if v is not None])
                abs_url = _build_api_url(abs_url, encoded_params)
        elif method in {"post", "put"}:
            if params and files:
                data = params
            if params and not files:
                data = json.dumps(params).encode()
                headers["Content-Type"] = "application/json"
        else:
            raise openai.APIConnectionError(
                message=f"Unrecognized HTTP method {method}. This may indicate a bug in the LLM bindings.",
                request=None,
            )

        headers = self.request_headers(method, headers, request_id)

        # log_debug("Request to LLM API", method=method, path=abs_url)
        # log_debug("Post details", data=data, api_version=self.api_version)

        return abs_url, headers, data

    def request_raw(
        self,
        method,
        url,
        *,
        params=None,
        supplied_headers: Optional[Dict[str, str]] = None,
        files=None,
        stream: bool = False,
        request_id: Optional[str] = None,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> requests.Response:
        abs_url, headers, data = self._prepare_request_raw(url, supplied_headers, method, params, files, request_id)

        if not hasattr(_thread_context, "session"):
            _thread_context.session = _make_session()
            _thread_context.session_create_time = time.time()
        elif time.time() - getattr(_thread_context, "session_create_time", 0) >= MAX_SESSION_LIFETIME_SECS:
            _thread_context.session.close()
            _thread_context.session = _make_session()
            _thread_context.session_create_time = time.time()
        try:
            result = _thread_context.session.request(
                method,
                abs_url,
                headers=headers,
                data=data,
                files=files,
                stream=stream,
                timeout=request_timeout if request_timeout else TIMEOUT_SECS,
                proxies=_thread_context.session.proxies,
            )
        except requests.exceptions.Timeout as e:
            raise openai.APITimeoutError("Request timed out: {}".format(e)) from e
        except requests.exceptions.RequestException as e:
            raise openai.APIConnectionError(message="Error communicating with LLM: {}".format(e), request=None) from e
        # log_debug(
        #     "LLM API response",
        #     path=abs_url,
        #     response_code=result.status_code,
        #     processing_ms=result.headers.get("LLM-Processing-Ms"),
        #     request_id=result.headers.get("X-Request-Id"),
        # )
        return result

    async def arequest_raw(
        self,
        method,
        url,
        session,
        *,
        params=None,
        supplied_headers: Optional[Dict[str, str]] = None,
        files=None,
        request_id: Optional[str] = None,
        request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> aiohttp.ClientResponse:
        abs_url, headers, data = self._prepare_request_raw(url, supplied_headers, method, params, files, request_id)

        if isinstance(request_timeout, tuple):
            timeout = aiohttp.ClientTimeout(
                connect=request_timeout[0],
                total=request_timeout[1],
            )
        else:
            timeout = aiohttp.ClientTimeout(total=request_timeout if request_timeout else TIMEOUT_SECS)

        if files:
            # TODO: Use `aiohttp.MultipartWriter` to create the multipart form data here.
            # For now we use the private `requests` method that is known to have worked so far.
            data, content_type = requests.models.RequestEncodingMixin._encode_files(files, data)  # type: ignore
            headers["Content-Type"] = content_type
        request_kwargs = {
            "method": method,
            "url": abs_url,
            "headers": headers,
            "data": data,
            "timeout": timeout,
        }
        try:
            result = await session.request(**request_kwargs)
            # log_info(
            #     "LLM API response",
            #     path=abs_url,
            #     response_code=result.status,
            #     processing_ms=result.headers.get("LLM-Processing-Ms"),
            #     request_id=result.headers.get("X-Request-Id"),
            # )
            return result
        except (aiohttp.ServerTimeoutError, asyncio.TimeoutError) as e:
            raise openai.APITimeoutError("Request timed out") from e
        except aiohttp.ClientError as e:
            raise openai.APIConnectionError(message="Error communicating with LLM", request=None) from e

    def _interpret_response(
        self, result: requests.Response, stream: bool
    ) -> Tuple[Union[OpenAIResponse, Iterator[OpenAIResponse]], bool]:
        """Returns the response(s) and a bool indicating whether it is a stream."""

    async def _interpret_async_response(
        self, result: aiohttp.ClientResponse, stream: bool
    ) -> Tuple[Union[OpenAIResponse, AsyncGenerator[OpenAIResponse, None]], bool]:
        """Returns the response(s) and a bool indicating whether it is a stream."""

    def _interpret_response_line(self, rbody: str, rcode: int, rheaders, stream: bool) -> OpenAIResponse:
        ...


@asynccontextmanager
async def aiohttp_session() -> AsyncIterator[aiohttp.ClientSession]:
    async with aiohttp.ClientSession() as session:
        yield session
