import json
from typing import Callable

from curl_cffi import requests

origin_request = requests.Session.request


class MockCurlCffiResponse(requests.Response):
    check_funcs: dict[tuple[str, str], Callable[[dict], str]] = {}
    rsp_cache: dict[str, str] = {}
    name = "curl-cffi"

    def __init__(self, session, method, url, **kwargs) -> None:
        super().__init__()
        fn = self.check_funcs.get((method, url))
        self.key = f"{self.name}-{method}-{url}-{fn(kwargs) if fn else json.dumps(kwargs, sort_keys=True)}"
        self.response = None
        if self.key not in self.rsp_cache:
            response = origin_request(session, method, url, **kwargs)
            self.rsp_cache[self.key] = response.content.decode()
        self.content = self.rsp_cache[self.key].encode()
