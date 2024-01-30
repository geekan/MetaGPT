import json
from typing import Callable
from urllib.parse import parse_qsl, urlparse

import httplib2

origin_request = httplib2.Http.request


class MockHttplib2Response(httplib2.Response):
    check_funcs: dict[tuple[str, str], Callable[[dict], str]] = {}
    rsp_cache: dict[str, str] = {}
    name = "httplib2"

    def __init__(self, http, uri, method="GET", **kwargs) -> None:
        url = uri.split("?")[0]
        result = urlparse(uri)
        params = dict(parse_qsl(result.query))
        fn = self.check_funcs.get((method, uri))
        new_kwargs = {"params": params}
        key = f"{self.name}-{method}-{url}-{fn(new_kwargs) if fn else json.dumps(new_kwargs)}"
        if key not in self.rsp_cache:
            _, self.content = origin_request(http, uri, method, **kwargs)
            self.rsp_cache[key] = self.content.decode()
        self.content = self.rsp_cache[key]

    def __iter__(self):
        yield self
        yield self.content.encode()
