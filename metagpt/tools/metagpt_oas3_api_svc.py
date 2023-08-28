#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/17
@Author  : mashenquan
@File    : metagpt_oas3_api_svc.py
@Desc    : MetaGPT OpenAPI Specification 3.0 REST API service
"""
import asyncio
from pathlib import Path
import sys

import connexion

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))  # fix-bug: No module named 'metagpt'
from metagpt.utils.common import initialize_environment


def oas_http_svc():
    """Start the OAS 3.0 OpenAPI HTTP service"""
    initialize_environment()

    app = connexion.AioHttpApp(__name__, specification_dir='../../.well-known/')
    app.add_api("metagpt_oas3_api.yaml")
    app.add_api("openapi.yaml")
    app.run(port=8080)


async def async_main():
    """Start the OAS 3.0 OpenAPI HTTP service in the background."""
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, oas_http_svc)

    # TODO: replace following codes:
    while True:
        await asyncio.sleep(1)
        print("sleep")


def main():
    oas_http_svc()


if __name__ == "__main__":
    # asyncio.run(async_main())
    main()
