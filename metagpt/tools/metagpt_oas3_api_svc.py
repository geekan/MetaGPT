#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/17
@Author  : mashenquan
@File    : metagpt_oas3_api_svc.py
@Desc    : MetaGPT OpenAPI Specification 3.0 REST API service
"""
from pathlib import Path
import sys
import connexion
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))  # fix-bug: No module named 'metagpt'
from metagpt.utils.common import initialize_environment

if __name__ == "__main__":
    initialize_environment()

    app = connexion.AioHttpApp(__name__, specification_dir='../../.well-known/')
    app.add_api("metagpt_oas3_api.yaml")
    app.add_api("openapi.yaml")
    app.run(port=8080)
