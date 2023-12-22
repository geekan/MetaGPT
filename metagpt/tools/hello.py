#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/2 16:03
@Author  : mashenquan
@File    : hello.py
@Desc    : Implement the OpenAPI Specification 3.0 demo and use the following command to test the HTTP service:

        curl -X 'POST' \
        'http://localhost:8080/openapi/greeting/dave' \
        -H 'accept: text/plain' \
        -H 'Content-Type: application/json' \
        -d '{}'
"""

import connexion


# openapi implement
async def post_greeting(name: str) -> str:
    return f"Hello {name}\n"


if __name__ == "__main__":
    app = connexion.AioHttpApp(__name__, specification_dir="../../.well-known/")
    app.add_api("openapi.yaml", arguments={"title": "Hello World Example"})
    app.run(port=8080)
