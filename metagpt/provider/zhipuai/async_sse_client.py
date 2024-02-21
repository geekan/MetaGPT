#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : async_sse_client to make keep the use of Event to access response
#           refs to `zhipuai/core/_sse_client.py`

import json
from typing import Any, Iterator


class AsyncSSEClient(object):
    """Asynchronous Server-Sent Events (SSE) client.

    This class provides an asynchronous iterator over server-sent events.

    Args:
        event_source: An iterator that yields bytes representing server-sent events.

    Attributes:
        _event_source: Stores the iterator that yields server-sent events.
    """

    def __init__(self, event_source: Iterator[Any]):
        self._event_source = event_source

    async def stream(self) -> dict:
        """Asynchronously streams data from the server-sent events.

        Yields:
            A dictionary representing a single server-sent event.

        Raises:
            RuntimeError: If the event source is a bytes object indicating a request failure.
        """
        if isinstance(self._event_source, bytes):
            raise RuntimeError(
                f"Request failed, msg: {self._event_source.decode('utf-8')}, please ref to `https://open.bigmodel.cn/dev/api#error-code-v3`"
            )
        async for chunk in self._event_source:
            line = chunk.decode("utf-8")
            if line.startswith(":") or not line:
                return

            field, _p, value = line.partition(":")
            if value.startswith(" "):
                value = value[1:]
            if field == "data":
                if value.startswith("[DONE]"):
                    break
                data = json.loads(value)
                yield data
