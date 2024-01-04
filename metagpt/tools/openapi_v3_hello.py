#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/2 16:03
@Author  : mashenquan
@File    : openapi_v3_hello.py
@Desc    : Implement the OpenAPI Specification 3.0 demo and use the following command to test the HTTP service:

        curl -X 'POST' \
        'http://localhost:8082/openapi/greeting/dave' \
        -H 'accept: text/plain' \
        -H 'Content-Type: application/json' \
        -d '{}'
"""
from pathlib import Path

import connexion


# openapi implement
async def post_greeting(name: str) -> str:
    return f"Hello {name}\n"


if __name__ == "__main__":
    specification_dir = Path(__file__).parent.parent.parent / "docs/.well-known"
    app = connexion.AsyncApp(__name__, specification_dir=str(specification_dir))
    app.add_api("openapi.yaml", arguments={"title": "Hello World Example"})
    app.run(port=8082)
