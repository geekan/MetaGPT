#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/17
@Author  : mashenquan
@File    : metagpt_oas3_api_svc.py
@Desc    : MetaGPT OpenAPI Specification 3.0 REST API service

        curl -X 'POST' \
        'http://localhost:8080/openapi/greeting/dave' \
        -H 'accept: text/plain' \
        -H 'Content-Type: application/json' \
        -d '{}'
"""

from pathlib import Path

import connexion


def oas_http_svc():
    """Start the OAS 3.0 OpenAPI HTTP service"""
    print("http://localhost:8080/oas3/ui/")
    specification_dir = Path(__file__).parent.parent.parent / "docs/.well-known"
    app = connexion.AsyncApp(__name__, specification_dir=str(specification_dir))
    app.add_api("metagpt_oas3_api.yaml")
    app.add_api("openapi.yaml")
    app.run(port=8080)


if __name__ == "__main__":
    oas_http_svc()
