import json
from typing import Callable

from aiohttp.client import ClientSession

origin_request = ClientSession.request


class MockAioResponse:
    check_funcs: dict[tuple[str, str], Callable[[dict], str]] = {}
    rsp_cache: dict[str, str] = {}
    name = "aiohttp"
    status = 200

    def __init__(self, session, method, url, **kwargs) -> None:
        fn = self.check_funcs.get((method, url))
        _kwargs = {k: v for k, v in kwargs.items() if k != "proxy"}
        self.key = f"{self.name}-{method}-{url}-{fn(kwargs) if fn else json.dumps(_kwargs, sort_keys=True)}"
        self.mng = self.response = None
        if self.key not in self.rsp_cache:
            self.mng = origin_request(session, method, url, **kwargs)

    async def __aenter__(self):
        if self.response:
            await self.response.__aenter__()
            self.status = self.response.status
        elif self.mng:
            self.response = await self.mng.__aenter__()
        return self

    async def __aexit__(self, *args, **kwargs):
        if self.response:
            await self.response.__aexit__(*args, **kwargs)
            self.response = None
        elif self.mng:
            await self.mng.__aexit__(*args, **kwargs)
            self.mng = None

    async def json(self, *args, **kwargs):
        if self.key in self.rsp_cache:
            return self.rsp_cache[self.key]
        data = await self.response.json(*args, **kwargs)
        self.rsp_cache[self.key] = data
        return data

    @property
    def content(self):
        return self

    async def read(self):
        if self.key in self.rsp_cache:
            return eval(self.rsp_cache[self.key])
        data = await self.response.content.read()
        self.rsp_cache[self.key] = str(data)
        return data

    def raise_for_status(self):
        if self.response:
            self.response.raise_for_status()
